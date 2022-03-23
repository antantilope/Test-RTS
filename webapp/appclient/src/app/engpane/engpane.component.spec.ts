import { ComponentFixture, TestBed } from '@angular/core/testing';

import { EngpaneComponent } from './engpane.component';

describe('EngpaneComponent', () => {
  let component: EngpaneComponent;
  let fixture: ComponentFixture<EngpaneComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ EngpaneComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(EngpaneComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
