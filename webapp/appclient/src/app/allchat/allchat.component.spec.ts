import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AllchatComponent } from './allchat.component';

describe('AllchatComponent', () => {
  let component: AllchatComponent;
  let fixture: ComponentFixture<AllchatComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ AllchatComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(AllchatComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
