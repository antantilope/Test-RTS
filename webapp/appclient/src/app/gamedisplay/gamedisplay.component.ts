import { Component, OnInit } from '@angular/core';
import { ApiService } from "../api.service";

@Component({
  selector: 'app-gamedisplay',
  templateUrl: './gamedisplay.component.html',
  styleUrls: ['./gamedisplay.component.css']
})
export class GamedisplayComponent implements OnInit {

  constructor(
    private _api: ApiService,
  ) {
    console.log("gamedisplay::constructor");
  }

  ngOnInit(): void {
  }

}
