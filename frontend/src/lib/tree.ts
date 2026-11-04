import type { CategoryNode, Paper } from "./types"

export function flattenCategories(nodes: CategoryNode[], depth = 0): Array<CategoryNode & { depth: number }> {
  const out: Array<CategoryNode & { depth: number }> = []
  for (const node of nodes) {
    out.push({ ...node, depth })
    out.push(...flattenCategories(node.children ?? [], depth + 1))
  }
  return out
}

export function mapPapersByCategory(papers: Paper[]): Record<string, Paper[]> {
  return papers.reduce<Record<string, Paper[]>>((acc, paper) => {
    const ids = Array.isArray(paper.category_ids) ? paper.category_ids : []
    if (!ids.length) {
      const key = "uncategorized"
      if (!acc[key]) {
        acc[key] = []
      }
      acc[key].push(paper)
      return acc
    }

    for (const categoryId of ids) {
      const key = String(categoryId)
      if (!acc[key]) {
        acc[key] = []
      }
      acc[key].push(paper)
    }
    return acc
  }, {})
}

export function formatAuthors(authors: string[]): string {
  if (!authors.length) {
    return "Unknown"
  }
  return authors.join(", ")
}
