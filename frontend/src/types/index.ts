export interface QueryResponse {
  answer: string;
  source_nodes: SourceNode[];
}

export interface SourceNode {
  text: string;
  score?: number;
  doc_id?: string;
  arxiv_url?: string;
}
