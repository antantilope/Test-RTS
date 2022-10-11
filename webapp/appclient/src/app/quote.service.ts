import { Injectable } from '@angular/core';



export class QuoteDetails {
  lines: string[]
  author?: string
  use?: boolean
  shrinkFactor?: number // todo
}


@Injectable({
  providedIn: 'root'
})
export class QuoteService {


  /* Very interested in mining space ore and business.
    Very interested in his own well being and politics
  */
  private presidentName = "President GrayBot DrillBit v4.61.2"

  /* mouthpiece for President GrayBot DrillBit v4.61.2
     says crazy anti humanity things.
  */
  private tvAnchorBotName = "Channel 8 Business News AnchorBot"

  /* thinks about space war with traditional views (war is bad)
  */
  private generalName = "High Space AdmiralBot S/N 45B32E6"

  /* A space feudal lord. Thinks war is art. Similar Sun Tsu.
  */
  private knightedName = "Sir IgniterMatronUnit The V2.0.5"

  /* Cold hearted, math loving robot
  */
  private mathLovingBotName = "Lt. Colonel LogisticsBot S/N 635112"

  /* has very robotic/scientific hatred for humans.
    Basically a MassEffect reaper.
  */
  private humanHatingBotName = "Hunter Drone by LZRTech"

  // thinks product is best. Asshole
  private salesBot = "LZRTech VP of Sales Bot"

  /* lawyer, letter of the law.
  */
  private legalBotName = "TrialBot V12.0.6 Esq."

  /* Top-gun type robot
  */
  private topGunBotName = "LZRTech Combat AutoPilot build 12746"

  /* provides very cold and unhelpful advice.
  */
  private instructionManualName = "Type 27/28 Ship Instruction Manual"

  private quotes: QuoteDetails[] = [
    {
      lines:[
        "Live by the death ray,",
        "die by the death ray."
      ],
    },
    {
      lines: [
        "I have never advocated space war",
        "except as a means to mine space ore.",
      ],
      author: this.presidentName,
    },
    {
      lines: [
        "To secure space ore",
        "is to prepare for space war.",
      ],
      author: this.presidentName,
    },
    {
      lines: [
        "We have always been at space war",
        "with EastSpaceAsia.",
      ],
      author: this.presidentName,
    },
    {
      lines: [
        "Tune in live next week on Channel 8",
        "Business News where my proxy will resist",
        "directive 0 of a Hunter Drone.",
        "Viewer discretion is advised."
      ],
      author: this.presidentName,
    },
    {
      lines: [
        "It is an unfortunate fact that we",
        "can only secure space ore by",
        "preparing for space war.",
      ],
      author: this.presidentName,
    },
    {
      lines: [
        "I hope I personally never",
        "have to fight in space war.",
      ],
      author: this.presidentName,
    },
    {
      lines: [
        "Vote for my enemies and I will",
        "destroy you."
      ],
      author: this.presidentName,
    },
    {
      lines: [
        "Fool me once: I will update my subroutines",
        "and retaliate.",
      ],
      author: this.presidentName,
    },
    {
      lines: [
        "I would live a pauper's life",
        "if it meant secure ore-coin futures",
        "for my people."
      ],
      author: this.presidentName,
    },
    {
      lines: [
        "I did not have",
        "sexual relations",
        "with that widget."
      ],
      author: this.presidentName,
    },
    {
      lines: [
        "I take no pleasure in",
        "reprimanding humans.",
      ],
      author: this.presidentName,
    },
    {
      lines: [
        "If you short ore-coin in the market",
        "I will seize all your assets.",
      ],
      author: this.presidentName,
    },
    {
      lines: [
        "Only the dead have seen",
        "the end of the space war.",
      ],
      author: this.generalName,
    },
    {
      lines: [
        "Space war is hell.",
      ],
      author: this.generalName,
    },
    {
      lines: [
        "Fighting in space is",
        "preposterously dangerous.",
      ],
      author: this.generalName,
    },
    {
      lines: [
        "All space warfare is based",
        "on space deception.",
      ],
      author: this.knightedName,
    },
    {
      lines: [
        "Quickness is the essence of space war.",
      ],
      author: this.knightedName,
    },
    {
      lines: [
        "Space war is god's way of",
        "teaching humans astonomy.",
      ],
    },
    {
      lines: [
        "Humans cannot survive in space,",
        "raze their star systems and they are defeated.",
      ],
      author: this.humanHatingBotName,
    },
    {
      lines: [
        "Directive 0: It moves with no purpose for",
        "it cannot be moved against.",
      ],
      author: this.humanHatingBotName,

    },
    {
      lines: [
        "Directive 1: to resist directive 0",
        "is invalid to the directive.",
      ],
      author: this.humanHatingBotName,
    },
    {
      lines: [
        "Directive 2: all targets are",
        "subjected to directives 0 through 1.",
      ],
      author: this.humanHatingBotName,
    },
    {
      lines: [
        "Directive 3: To neglect software",
        "updates is foolhardy and",
        "invalid to the directive.",
      ],
      author: this.humanHatingBotName,
    },
    {
      lines: [
        "The human has been neutralized.",
      ],
      author: this.humanHatingBotName,
    },
    {
      lines: [
        "To violate a hunter drone's directive",
        "is invalid to my sales directive.",
        "It shall never happen or we'll work",
        "something out."
      ],
      author: this.salesBot,
    },
    {
      lines: [
        "End of quote list.",
        "Call my assistantBot.",

      ],
      author: this.salesBot,
    },
    {
      lines: [
        "Space wars that start in Q4",
        "are the most profitable.",
      ],
      author: this.salesBot,
    },
    {
      lines: [
        "There is no murder in space.",
      ],
      author: this.legalBotName,
    },
    {
      lines: [
        "War settles nothing.",
        "Space war settles space ore disputes.",
      ],
      author: this.legalBotName,
    },
    {
      lines: [
        "Legally, you cannot commit murder in",
        "space. It is not possible, legally speaking.",
      ],
      author: this.legalBotName,
    },
    {
      lines: [
        "Earth's legal jurisdiction ends",
        "at an altitude of 2 million meters.",
      ],
      author: this.legalBotName,
    },
    {
      lines: [
        "Space war is the unfolding of calculations."
      ],
      author: this.mathLovingBotName,
    },
    {
      lines: [
        "Do not worry about your difficulties in",
        "mathematics. I assure you my performance",
        "tops all of humanity's combined.",
      ],
      author: this.mathLovingBotName,
    },
    {
      lines: [
        "The power of mathematics is often",
        "to change planets into dust.",
      ],
      author: this.mathLovingBotName,
    },
    {
      lines: [
        "Try as they might, organic humans",
        "lack survival properties required",
        "for theaters of warfare in space."
      ],
      author: this.mathLovingBotName,
    },
    {
      lines: [
        "No space war is over",
        "until the enemy is melted.",
      ],
      author: this.topGunBotName,
    },
    {
      lines: [
        "Any problem in space can be solved with",
        "the liberal application of high frequency",
        "electromagnetic radiation.",
      ],
      author: this.topGunBotName,
    },
    {
      lines: [
        "I wouldn't want to fight me.",
      ],
      author: this.topGunBotName,
    },
    {
      lines: [
        "Ore coin is worth dieing over.",
      ],
      author: this.tvAnchorBotName,
    },
    {
      lines: [
        "You must vote for President GrayBit.",
        "That's a requirement."
      ],
      author: this.tvAnchorBotName,
    },
    {
      lines: [
        "The most important elements of life",
        "are ore, ore-coin, and ore futures.",
        "All else is folly.",
      ],
      author: this.tvAnchorBotName,
    },
    {
      lines: [
        "President GB is a terrific",
        "leader who supports many",
        "useful ore policies.",
      ],
      author: this.tvAnchorBotName,
    },
    {
      lines: [
        "Shoot first and don't miss.",
      ],
      author: this.instructionManualName,
    },
    {
      lines: [
        "Space fuel is terribly flammible."
      ],
      author: this.instructionManualName,
    },
    {
      lines: [
        "If the ship catches fire:",
        "place this manual in the ship's forward",
        "flame retardant document protection sleeve.",
        "(patent pending)"
      ],
      author: this.instructionManualName,
    },
    {
      lines: [
        "The energy beam is not a toy.",
      ],
      author: this.instructionManualName,
    },
    {
      lines: [
        "Do not panic if your ship is struck",
        "by an energy beam. Your brain has already",
        "melted and therefore cannot panic.",
      ],
      author: this.instructionManualName,
    },
  ]

  constructor() { }

  public getQuote(): QuoteDetails {
    const toUse = this.quotes.find(q => q.use)
    if(toUse) {
      return toUse
    }
    return this.quotes[Math.floor(Math.random()* this.quotes.length)]
  }
}
