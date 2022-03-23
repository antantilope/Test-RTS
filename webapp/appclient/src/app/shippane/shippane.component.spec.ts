import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ShippaneComponent } from './shippane.component';

describe('ShippaneComponent', () => {
  let component: ShippaneComponent;
  let fixture: ComponentFixture<ShippaneComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ShippaneComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ShippaneComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
