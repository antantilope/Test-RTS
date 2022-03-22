import { TestBed } from '@angular/core/testing';

import { AllchatService } from './allchat.service';

describe('AllchatService', () => {
  let service: AllchatService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(AllchatService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
