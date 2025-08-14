import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { BrandData } from '../services/brand-data';
import { BrandPulseData } from '../models/brand-data.model';

@Component({
  selector: 'app-brand-pulse',
  imports: [CommonModule],
  templateUrl: './brand-pulse.html',
  styleUrl: './brand-pulse.css'
})
export class BrandPulse implements OnInit, OnDestroy {
  brandData: BrandPulseData | null = null;
  private subscription: Subscription | null = null;

  constructor(private brandDataService: BrandData) {}

  ngOnInit(): void {
    this.subscription = this.brandDataService.getBrandData().subscribe(
      data => {
        this.brandData = data;
      },
      error => {
        console.error('Error loading brand data:', error);
        // Fallback to default data
        this.brandData = {
          sentiment: { positive: 65, negative: 20, neutral: 15 },
          distribution: { positive: 70, negative: 90, neutral: 60 },
          lastUpdated: new Date()
        };
      }
    );
  }

  ngOnDestroy(): void {
    if (this.subscription) {
      this.subscription.unsubscribe();
    }
  }
}
