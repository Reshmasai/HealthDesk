import { Component } from '@angular/core';

@Component({
  selector: 'app-health-query',
  templateUrl: './health-query.component.html'
})
export class HealthQueryComponent {
  name = '';
  symptoms = '';
  severity = 'Low';

  submit() {
    console.log({
      name: this.name,
      symptoms: this.symptoms,
      severity: this.severity
    });
  }
}