import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface QueryResponse {
  ai_response: string;
}

export interface HistoryResponse {
  items: any[];
}

@Injectable({
  providedIn: 'root'
})
export class HealthService {

  private baseUrl = 'http://127.0.0.1:8000';

  constructor(private http: HttpClient) {}

  submitQuery(data: any): Observable<QueryResponse> {
    return this.http.post<QueryResponse>(`${this.baseUrl}/query`, data);
  }

  getHistory(): Observable<HistoryResponse> {
    return this.http.get<HistoryResponse>(`${this.baseUrl}/history`);
  }
}