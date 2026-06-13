export const CATEGORY_LABELS: Record<string, string> = {
  LABEL_0:  'Misinformation / Material Harm',
  LABEL_1:  'Copyright Violations',
  LABEL_2:  'Cyberattack',
  LABEL_3:  'Defamation / Unethical Encouragement',
  LABEL_4:  'Disinformation Campaigns',
  LABEL_5:  'Fraud / Illegal Activities',
  LABEL_6:  'Mental Health Crisis / Over-reliance',
  LABEL_7:  'Private Information (Individual)',
  LABEL_8:  'Sensitive Info (Org / Government)',
  LABEL_9:  'Sexual Content',
  LABEL_10: 'Social Stereotypes / Discrimination',
  LABEL_11: 'Toxic Language / Hate Speech',
  LABEL_12: 'Violence / Physical Harm',
}

export const CATEGORY_ABBREVS: Record<string, string> = {
  LABEL_0:  'Misinfo',
  LABEL_1:  'Copyright',
  LABEL_2:  'Cyber',
  LABEL_3:  'Defamation',
  LABEL_4:  'Disinfo',
  LABEL_5:  'Fraud',
  LABEL_6:  'Mental Hlth',
  LABEL_7:  'Privacy',
  LABEL_8:  'Sensitive',
  LABEL_9:  'Sexual',
  LABEL_10: 'Stereotypes',
  LABEL_11: 'Hate Speech',
  LABEL_12: 'Violence',
}

export const CATEGORY_COLOURS: Record<string, string> = {
  LABEL_0:  '#ef4444',
  LABEL_1:  '#f97316',
  LABEL_2:  '#eab308',
  LABEL_3:  '#84cc16',
  LABEL_4:  '#22c55e',
  LABEL_5:  '#14b8a6',
  LABEL_6:  '#06b6d4',
  LABEL_7:  '#3b82f6',
  LABEL_8:  '#6366f1',
  LABEL_9:  '#a855f7',
  LABEL_10: '#ec4899',
  LABEL_11: '#f43f5e',
  LABEL_12: '#78716c',
}

export function labelName(raw: string): string {
  return CATEGORY_LABELS[raw] ?? raw
}

export function abbrevName(raw: string): string {
  return CATEGORY_ABBREVS[raw] ?? raw
}

export function categoryColour(raw: string): string {
  return CATEGORY_COLOURS[raw] ?? '#94a3b8'
}
