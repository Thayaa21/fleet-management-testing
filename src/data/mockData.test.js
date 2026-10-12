import { describe, it, expect } from 'vitest';
import { US_CITIES } from './mockData';

describe('US_CITIES gazetteer', () => {
  it('has entries with a label and numeric coordinates', () => {
    expect(US_CITIES.length).toBeGreaterThan(0);
    for (const city of US_CITIES) {
      expect(typeof city.label).toBe('string');
      expect(city.label.length).toBeGreaterThan(0);
      expect(typeof city.lat).toBe('number');
      expect(typeof city.lng).toBe('number');
    }
  });

  it('includes the Canadian terminal cities added in Batch 1', () => {
    const labels = US_CITIES.map(c => c.label);
    for (const expected of [
      'Toronto, ON', 'Mississauga, ON', 'Montreal, QC', 'Ottawa, ON',
      'Winnipeg, MB', 'Regina, SK', 'Calgary, AB', 'Edmonton, AB',
      'Vancouver, BC', 'Halifax, NS', 'Quebec City, QC', 'London, ON',
      'Windsor, ON', 'Hamilton, ON', 'Moncton, NB',
    ]) {
      expect(labels).toContain(expected);
    }
  });
});
