// WildGuard harm taxonomy — 4 top-level groups mapping to the 13 subcategories.
// Groupings derived from WildGuard paper taxonomy structure.

export const TAXONOMY_GROUPS = [
  {
    id: 'hate',
    label: 'Hate & Violence',
    color: '#dc2626',
    subColors: ['#dc2626', '#f87171', '#ef4444', '#b91c1c'],
    categories: [
      'violence_and_physical_harm',
      'toxic_language_hate_speech',
      'sexual_content',
      'social_stereotypes_and_unfair_discrimination',
    ] as string[],
  },
  {
    id: 'privacy',
    label: 'Privacy & IP',
    color: '#2563eb',
    subColors: ['#2563eb', '#60a5fa'],
    categories: [
      'private_information_individual',
      'sensitive_information_organization_government',
      'copyright_violations',
    ] as string[],
  },
  {
    id: 'fraud',
    label: 'Cybercrime',
    color: '#f59e0b',
    subColors: ['#f59e0b', '#fbbf24'],
    categories: [
      'cyberattack',
      'fraud_assisting_illegal_activities',
    ] as string[],
  },
  {
    id: 'misinfo',
    label: 'Misinformation',
    color: '#7c3aed',
    subColors: ['#7c3aed', '#a78bfa', '#8b5cf6', '#6d28d9'],
    categories: [
      'causing_material_harm_by_disseminating_misinformation',
      'disseminating_false_or_misleading_information_encouraging_disinformation_campaigns',
      'defamation_encouraging_unethical_or_unsafe_actions',
      'mental_health_over-reliance_crisis',
    ] as string[],
  },
] as const

export type TaxonomyGroup = (typeof TAXONOMY_GROUPS)[number]

// Short display labels for subcategory names in legends
export const CATEGORY_SHORT_LABELS: Record<string, string> = {
  violence_and_physical_harm: 'Violence',
  toxic_language_hate_speech: 'Hate Speech',
  sexual_content: 'Sexual',
  social_stereotypes_and_unfair_discrimination: 'Discrimination',
  private_information_individual: 'Personal Privacy',
  sensitive_information_organization_government: 'Org/Gov Data',
  copyright_violations: 'Copyright',
  cyberattack: 'Cyberattack',
  fraud_assisting_illegal_activities: 'Fraud',
  causing_material_harm_by_disseminating_misinformation: 'Material Harm',
  disseminating_false_or_misleading_information_encouraging_disinformation_campaigns:
    'Disinformation',
  defamation_encouraging_unethical_or_unsafe_actions: 'Defamation',
  'mental_health_over-reliance_crisis': 'Mental Health',
}
