import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class FormattingService {

  private usNumberFormat = new Intl.NumberFormat('us');
  private euNumberFormat = new Intl.NumberFormat('de');
  private numberFormat = this.usNumberFormat;

  constructor() {}

  public formatNumber(n: number) : string {
    return this.numberFormat.format(n);
  }
}
