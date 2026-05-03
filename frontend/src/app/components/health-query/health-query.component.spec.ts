import { ComponentFixture, TestBed } from '@angular/core/testing';

import { HealthQueryComponent } from './health-query.component';

describe('HealthQueryComponent', () => {
  let component: HealthQueryComponent;
  let fixture: ComponentFixture<HealthQueryComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ HealthQueryComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(HealthQueryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
