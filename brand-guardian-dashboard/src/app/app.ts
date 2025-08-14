import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { BrandPulse } from './brand-pulse/brand-pulse';
import { HttpClientModule } from '@angular/common/http';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, BrandPulse, HttpClientModule],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  protected title = 'brand-guardian-dashboard';
}
