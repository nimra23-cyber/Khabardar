/** Shared API payload types (Task 2.14). Mirror the backend DetectResult. */

export type Classification = "SAFE" | "SUSPICIOUS" | "HIGH RISK";

export interface DetectSignal {
  signal_id: string;
  name: string;
  explanation: string;
  direction: string;
  evidence: string[];
  languages: string[];
}

export interface DetectResult {
  risk_score: number;
  classification: Classification;
  category: string | null;
  signals: DetectSignal[];
  explanation_en: string;
  explanation_ur: string;
  confidence: number;
  detected_languages: string[];
  no_signals_detected: boolean;
  no_signal_notice: string | null;
  ruleset_version: string;
  timestamp: string;
  scan_id: string | null;
  save_error: boolean;
}

export interface HistoryItem {
  id: string;
  scan_type: string;
  masked_content: string | null;
  risk_score: number | null;
  classification: Classification | null;
  category: string | null;
  confidence: number | null;
  created_at: string | null;
}

export interface HistoryResponse {
  items: HistoryItem[];
  count: number;
}


export interface URLIndicator {
  id: string;
  name: string;
  evidence: string;
  weight: number;
}

export interface URLAnalysisResult {
  url: string;
  domain: string;
  scheme: string;
  is_ip_url: boolean;
  blocked: boolean;
  risk_score: number;
  classification: Classification;
  indicators: URLIndicator[];
  integration_states: Record<string, string>;
  redirect_chain: string[];
  network_checks: string;
  recommended_action: string;
  explanation_en: string;
  ruleset_version: string;
}


export interface TrendPoint {
  date: string;
  count: number;
}

export interface DashboardStats {
  total_scans: number;
  detected_scams: number;
  risk_distribution: Record<string, number>;
  category_breakdown: Record<string, number>;
  trend_30d: TrendPoint[];
  empty: boolean;
  public_demo: boolean;
  environment: string;
}

export interface IOCItem {
  ioc_type: string;
  display_value: string;
  note: string;
}

export interface IOCExtractResult {
  count: number;
  iocs: IOCItem[];
  integration_states: Record<string, string>;
  note: string;
}


export interface ReportResult {
  report: Record<string, unknown>;
  markdown: string;
  filename: string;
}

// --- Media Scanner types (Req 12) ---

export interface OCROutput {
  available: boolean;
  text: string | null;
  error: string | null;
}

export interface QROutput {
  available: boolean;
  values: string[];
  error: string | null;
}

export interface MediaScanResult {
  ocr: OCROutput;
  qr: QROutput;
  urls_found: string[];
  text_analysis: DetectResult | null;
  url_analyses: Array<URLAnalysisResult | { valid: false; reason: string }>;
  image_type: "png" | "jpeg" | "webp";
  public_demo: boolean;
}
