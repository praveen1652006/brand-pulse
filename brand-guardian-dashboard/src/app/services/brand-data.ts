import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject, interval } from 'rxjs';
import { switchMap, catchError } from 'rxjs/operators';
import { BrandPulseData } from '../models/brand-data.model';

@Injectable({
  providedIn: 'root'
})
export class BrandData {
  private dataSubject = new BehaviorSubject<BrandPulseData>({
    sentiment: { positive: 65, negative: 20, neutral: 15 },
    distribution: { positive: 70, negative: 90, neutral: 60 },
    lastUpdated: new Date()
  });

  public data$ = this.dataSubject.asObservable();

  constructor(private http: HttpClient) {
    // Poll for updates every 30 seconds
    interval(30000).pipe(
      switchMap(() => this.fetchBrandData()),
      catchError(error => {
        console.error('Error fetching brand data:', error);
        return this.data$;
      })
    ).subscribe(data => {
      if (data) {
        this.dataSubject.next(data);
      }
    });
  }

  private fetchBrandData(): Observable<BrandPulseData> {
    // This will connect to your Python backend
    return this.http.get<BrandPulseData>('http://localhost:5000/api/brand-sentiment');
  }

  getBrandData(): Observable<BrandPulseData> {
    return this.data$;
  }
}
