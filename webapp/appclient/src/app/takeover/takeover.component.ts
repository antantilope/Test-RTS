import { Component, OnInit } from '@angular/core';
import { ApiService } from "../api.service";


@Component({
  selector: 'app-takeover',
  templateUrl: './takeover.component.html',
  styleUrls: ['./takeover.component.css']
})
export class TakeoverComponent implements OnInit {

  constructor(
    private _api: ApiService,
  ) {
    console.log("takeover::constructor");
  }

  ngOnInit(): void {
  }

}
