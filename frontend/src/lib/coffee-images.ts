const imagePool = [
  '/images/coffee/coffee-01.jpg',
  '/images/coffee/coffee-02.jpg',
  '/images/coffee/coffee-03.jpg',
  '/images/coffee/coffee-04.jpg',
  '/images/coffee/coffee-05.jpg',
  '/images/coffee/coffee-06.jpg',
  '/images/coffee/coffee-07.jpg',
  '/images/coffee/coffee-08.jpg'
] as const;

const preferredBySlug: Record<string, (typeof imagePool)[number]> = {
  'yirgacheffe-reserve': '/images/coffee/coffee-01.jpg',
  'huila-valley': '/images/coffee/coffee-02.jpg',
  'antigua-sunrise': '/images/coffee/coffee-03.jpg',
  'nyeri-aa': '/images/coffee/coffee-04.jpg'
};

export function coffeeImageFor(slug: string, index: number): string {
  return preferredBySlug[slug] ?? imagePool[index % imagePool.length];
}
