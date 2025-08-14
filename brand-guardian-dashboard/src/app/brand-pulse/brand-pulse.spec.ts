import { ComponentFixture, TestBed } from '@angular/core/testing';

import { BrandPulse } from './brand-pulse';

describe('BrandPulse', () => {
  let component: BrandPulse;
  let fixture: ComponentFixture<BrandPulse>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [BrandPulse]
    })
    .compileComponents();

    fixture = TestBed.createComponent(BrandPulse);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
