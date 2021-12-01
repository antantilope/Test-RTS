import { TestBed } from '@angular/core/testing';

import { PaneService } from './pane.service';

describe('PaneService', () => {
  let service: PaneService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(PaneService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
