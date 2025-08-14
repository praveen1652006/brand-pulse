export interface SentimentData {
  positive: number;
  negative: number;
  neutral: number;
}

export interface SentimentDistribution {
  positive: number;
  negative: number;
  neutral: number;
}

export interface BrandPulseData {
  sentiment: SentimentData;
  distribution: SentimentDistribution;
  lastUpdated: Date;
}
