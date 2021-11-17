import { TestBed } from '@angular/core/testing';

import { TakeoverService } from './takeover.service';

describe('TakeoverService', () => {
  let service: TakeoverService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(TakeoverService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
