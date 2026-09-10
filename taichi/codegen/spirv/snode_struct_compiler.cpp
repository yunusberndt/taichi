#include "taichi/codegen/spirv/snode_struct_compiler.h"

#include <algorithm>

namespace taichi::lang {
namespace spirv {
namespace {

// Buffer accesses index the root buffer as an array of the accessed primitive:
// `at_buffer` in spirv_codegen.cpp turns a byte offset into an element index
// with a right shift by log2(sizeof(primitive)). That shift truncates, so a
// place SNode sitting at an offset that is not a multiple of its primitive size
// would be read and written one slot too low, aliasing the last element of the
// field placed before it. The two helpers below keep every place SNode on its
// natural boundary, at a cost of at most `alignment - 1` padding bytes per
// field.
inline std::size_t primitive_alignment(std::size_t size_bytes) {
  // Largest power of two not exceeding |size_bytes|, capped at 8 bytes, which
  // is the widest primitive we emit array views for.
  std::size_t alignment = 1;
  while (alignment * 2 <= size_bytes && alignment < 8) {
    alignment *= 2;
  }
  return alignment;
}

inline std::size_t align_up(std::size_t offset, std::size_t alignment) {
  // |alignment| is always a power of two here.
  return (offset + alignment - 1) & ~(alignment - 1);
}

class StructCompiler {
 public:
  CompiledSNodeStructs run(SNode &root) {
    TI_ASSERT(root.type == SNodeType::root);

    CompiledSNodeStructs result;
    result.root = &root;
    result.root_size = compute_snode_size(&root);
    result.snode_descriptors = std::move(snode_descriptors_);
    /*
    result.type_factory = new tinyir::Block;
    result.root_type = construct(*result.type_factory, &root);
    */
    TI_TRACE("RootBuffer size={}", result.root_size);

    /*
    std::unique_ptr<tinyir::Block> b = ir_reduce_types(result.type_factory);

    TI_WARN("Original types:\n{}", ir_print_types(result.type_factory));

    TI_WARN("Reduced types:\n{}", ir_print_types(b.get()));
    */

    return result;
  }

 private:
  const tinyir::Type *construct(tinyir::Block &ir_module, SNode *sn) {
    const tinyir::Type *cell_type = nullptr;

    if (sn->is_place()) {
      // Each cell is a single Type
      cell_type = translate_ti_primitive(ir_module, sn->dt);
    } else {
      // Each cell is a struct
      std::vector<const tinyir::Type *> struct_elements;
      for (auto &ch : sn->ch) {
        const tinyir::Type *elem_type = construct(ir_module, ch.get());
        struct_elements.push_back(elem_type);
      }
      tinyir::Type *st = ir_module.emplace_back<StructType>(struct_elements);
      st->set_debug_name(
          fmt::format("{}_{}", snode_type_name(sn->type), sn->get_name()));
      cell_type = st;

      if (sn->type == SNodeType::pointer) {
        cell_type = ir_module.emplace_back<PhysicalPointerType>(cell_type);
      }
    }

    if (sn->num_cells_per_container == 1 || sn->is_scalar()) {
      return cell_type;
    } else {
      return ir_module.emplace_back<ArrayType>(cell_type,
                                               sn->num_cells_per_container);
    }
  }

  std::size_t compute_snode_size(SNode *sn) {
    const bool is_place = sn->is_place();

    SNodeDescriptor sn_desc;
    sn_desc.snode = sn;
    if (is_place) {
      sn_desc.cell_stride = data_type_size(sn->dt);
      sn_desc.container_stride = sn_desc.cell_stride;
      sn_desc.alignment = primitive_alignment(sn_desc.cell_stride);
    } else {
      // Sort by size, so that smaller subfields are placed first.
      // This accelerates Nvidia's GLSL compiler, as the compiler tries to
      // place all statically accessed fields
      std::vector<std::pair<size_t, int>> element_strides;
      int i = 0;
      for (auto &ch : sn->ch) {
        element_strides.push_back({compute_snode_size(ch.get()), i});
        i += 1;
      }
      std::sort(
          element_strides.begin(), element_strides.end(),
          [](const std::pair<size_t, int> &a, const std::pair<size_t, int> &b) {
            return a.first < b.first;
          });

      std::size_t cell_stride = 0;
      std::size_t cell_alignment = 1;
      for (auto &[snode_size, i] : element_strides) {
        auto &ch = sn->ch[i];
        auto *ch_snode = ch.get();
        const std::size_t ch_alignment =
            snode_descriptors_.find(ch_snode->id)->second.alignment;
        cell_alignment = std::max(cell_alignment, ch_alignment);
        cell_stride = align_up(cell_stride, ch_alignment);
        auto child_offset = cell_stride;
        cell_stride += snode_size;
        snode_descriptors_.find(ch_snode->id)
            ->second.mem_offset_in_parent_cell = child_offset;
        ch_snode->offset_bytes_in_parent_cell = child_offset;
      }
      // Cells of a container sit back to back, so the stride itself has to
      // preserve the alignment of the strictest child; otherwise only cell 0
      // would be aligned.
      cell_stride = align_up(cell_stride, cell_alignment);
      sn_desc.cell_stride = cell_stride;
      sn_desc.alignment = cell_alignment;

      if (sn->type == SNodeType::bitmasked) {
        size_t num_cells = sn_desc.snode->num_cells_per_container;
        size_t bitmask_num_words =
            num_cells % 32 == 0 ? (num_cells / 32) : (num_cells / 32 + 1);
        sn_desc.container_stride =
            cell_stride * num_cells + bitmask_num_words * 4;
      } else {
        sn_desc.container_stride =
            cell_stride * sn_desc.snode->num_cells_per_container;
      }
    }

    sn->cell_size_bytes = sn_desc.cell_stride;

    sn_desc.total_num_cells_from_root = 1;
    for (const auto &e : sn->extractors) {
      // Note that the extractors are set in two places:
      // 1. When a new SNode is first defined
      // 2. StructCompiler::infer_snode_properties()
      // The second step is the finalized result.
      sn_desc.total_num_cells_from_root *= e.num_elements_from_root;
    }

    TI_TRACE("SNodeDescriptor");
    TI_TRACE("* snode={}", sn_desc.snode->id);
    TI_TRACE("* type={} (is_place={})", sn_desc.snode->node_type_name,
             is_place);
    TI_TRACE("* cell_stride={}", sn_desc.cell_stride);
    TI_TRACE("* num_cells_per_container={}",
             sn_desc.snode->num_cells_per_container);
    TI_TRACE("* container_stride={}", sn_desc.container_stride);
    TI_TRACE("* total_num_cells_from_root={}",
             sn_desc.total_num_cells_from_root);
    TI_TRACE("");

    TI_ASSERT(snode_descriptors_.find(sn->id) == snode_descriptors_.end());
    snode_descriptors_[sn->id] = sn_desc;
    return sn_desc.container_stride;
  }

  SNodeDescriptorsMap snode_descriptors_;
};

}  // namespace

CompiledSNodeStructs compile_snode_structs(SNode &root) {
  StructCompiler compiler;
  return compiler.run(root);
}

}  // namespace spirv
}  // namespace taichi::lang
