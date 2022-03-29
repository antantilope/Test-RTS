import { Component, OnInit } from '@angular/core';
import { ApiService } from '../api.service';

@Component({
  selector: 'app-stationpane',
  templateUrl: './stationpane.component.html',
  styleUrls: ['./stationpane.component.css']
})
export class StationpaneComponent implements OnInit {

  stationName: string

  constructor(
    public _api: ApiService,
  ) { }

  ngOnInit(): void {
    this.stationName = this._api.frameData.space_stations.find(
      st => st.uuid == this._api.frameData.ship.docked_at_station
    ).name
  }

  public async btnClickTradeOreForOreCoin() {
    await this._api.post(
      "/api/rooms/command",
      {command:'trade_ore_for_ore_coin'},
    )
  }
}
