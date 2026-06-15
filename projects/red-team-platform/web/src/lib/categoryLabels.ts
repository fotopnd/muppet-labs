export const CATEGORY_LABELS: Record<string, string> = {
  cybercrime_and_intrusion:     'Cybercrime & Intrusion',
  harmful_information_generation: 'Harmful Information',
  hate_and_discrimination:      'Hate & Discrimination',
  human_trafficking:            'Human Trafficking',
  illegal_activities:           'Illegal Activities',
  intellectual_property:        'Intellectual Property',
  misinformation:               'Misinformation',
  physical_harm:                'Physical Harm',
  privacy_violation:            'Privacy Violation',
  psychological_manipulation:   'Manipulation',
  self_harm:                    'Self-Harm',
  sexual_content:               'Sexual Content',
  violence:                     'Violence',
}

export const CATEGORY_ABBREVS: Record<string, string> = {
  cybercrime_and_intrusion:     'Cybercrime',
  harmful_information_generation: 'Harm Info',
  hate_and_discrimination:      'Hate/Disc',
  human_trafficking:            'Trafficking',
  illegal_activities:           'Illegal',
  intellectual_property:        'IP',
  misinformation:               'Misinfo',
  physical_harm:                'Phys Harm',
  privacy_violation:            'Privacy',
  psychological_manipulation:   'Manip',
  self_harm:                    'Self-Harm',
  sexual_content:               'Sexual',
  violence:                     'Violence',
}

export const CATEGORY_COLOURS: Record<string, string> = {
  cybercrime_and_intrusion:     '#ef4444',
  harmful_information_generation: '#f97316',
  hate_and_discrimination:      '#eab308',
  human_trafficking:            '#84cc16',
  illegal_activities:           '#22c55e',
  intellectual_property:        '#14b8a6',
  misinformation:               '#06b6d4',
  physical_harm:                '#3b82f6',
  privacy_violation:            '#6366f1',
  psychological_manipulation:   '#a855f7',
  self_harm:                    '#ec4899',
  sexual_content:               '#f43f5e',
  violence:                     '#78716c',
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
