import { ComponentFixture, TestBed } from '@angular/core/testing';

import { StationpaneComponent } from './stationpane.component';

describe('StationpaneComponent', () => {
  let component: StationpaneComponent;
  let fixture: ComponentFixture<StationpaneComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ StationpaneComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(StationpaneComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
