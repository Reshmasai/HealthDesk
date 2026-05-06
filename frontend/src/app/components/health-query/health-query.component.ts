import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import { HealthService } from '../../services/health.service';

interface Message {
  role: 'user' | 'ai';
  text: string;
  severity?: string;
}

@Component({
  selector: 'app-health-query',
  templateUrl: './health-query.component.html',
  styleUrls: ['./health-query.component.scss']
})
export class HealthQueryComponent implements OnInit {

  name = '';
  symptoms = '';
  severity = 'Low';

  messages: Message[] = [];
  loading = false;

  @ViewChild('chatContainer') chatContainer!: ElementRef;

  constructor(private healthService: HealthService) {}

  ngOnInit(): void {
    this.loadHistory();
  }

  loadHistory() {
    this.healthService.getHistory().subscribe(res => {
      const items = res.items || [];
      this.messages = items.map((i: any) => ({
        role: i.role,
        text: i.text,
        severity: i.severity
      }));
      this.scrollToBottom();
    });
  }

  send() {
    if (!this.symptoms?.trim()) return;

    const payload = {
      name: this.name || 'User',
      symptoms: this.symptoms,
      severity: this.severity
    };

    this.messages.push({
      role: 'user',
      text: this.symptoms,
      severity: this.severity
    });

    this.scrollToBottom();
    this.symptoms = '';
    this.loading = true;

    this.healthService.submitQuery(payload).subscribe({
      next: (res: any) => {
        this.messages.push({ role: 'ai', text: res.ai_response });
        this.scrollToBottom();
        this.loading = false;
      },
      error: () => {
        this.messages.push({ role: 'ai', text: 'Error processing request.' });
        this.scrollToBottom();
        this.loading = false;
      }
    });
  }

  scrollToBottom() {
    setTimeout(() => {
      if (this.chatContainer?.nativeElement) {
        this.chatContainer.nativeElement.scrollTop =
          this.chatContainer.nativeElement.scrollHeight;
      }
    }, 50);
  }
}