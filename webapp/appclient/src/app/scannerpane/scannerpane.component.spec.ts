import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ScannerpaneComponent } from './scannerpane.component';

describe('ScannerpaneComponent', () => {
  let component: ScannerpaneComponent;
  let fixture: ComponentFixture<ScannerpaneComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ScannerpaneComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ScannerpaneComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
