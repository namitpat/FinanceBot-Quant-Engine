import { Component } from '@angular/core';
import { FormBuilder } from '@angular/forms';
import { formatCents } from '@fmt/format';
import limits from '../../../config/limits.json';

@Component({
  selector: 'app-portfolio',
  templateUrl: './portfolio.component.html',
  styleUrls: ['./portfolio.component.scss'],
})
export class PortfolioComponent {
  reportUrl = '';
  form = this.fb.group({ symbol: [''], qty: [1] });

  constructor(private fb: FormBuilder) {}

  total(priceCents: number): string {
    const qty = this.form.value.qty ?? 0;
    if (qty * priceCents > limits.maxOrderCents) {
      return 'over limit';
    }
    return formatCents(qty * priceCents);
  }
}
