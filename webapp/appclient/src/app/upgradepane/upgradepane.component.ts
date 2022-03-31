import { Component, OnInit } from '@angular/core';
import { ApiService } from '../api.service';

@Component({
  selector: 'app-upgradepane',
  templateUrl: './upgradepane.component.html',
  styleUrls: ['./upgradepane.component.css']
})
export class UpgradepaneComponent implements OnInit {

  constructor(
    public _api: ApiService,
  ) { }

  ngOnInit(): void {
  }

  public async btnStartAdvancedElectronicsUpgrade() {
    await this._api.post(
      "/api/rooms/command",
      {
        command:'start_core_upgrade',
        slug: 'advanced_electronics',
      },
    )
  }

}
