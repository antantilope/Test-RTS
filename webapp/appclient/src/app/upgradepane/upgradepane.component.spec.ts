import { ComponentFixture, TestBed } from '@angular/core/testing';

import { UpgradepaneComponent } from './upgradepane.component';

describe('UpgradepaneComponent', () => {
  let component: UpgradepaneComponent;
  let fixture: ComponentFixture<UpgradepaneComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ UpgradepaneComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(UpgradepaneComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
