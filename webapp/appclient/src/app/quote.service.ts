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
  private presidentName = "President GrayBot DrillBit"

  /* mouthpiece for President GrayBot DrillBit v4.61.2
     says crazy anti humanity things.
  */
  private tvAnchorBotName = "Channel 8 Business News AnchorBot"

  /* thinks about space war with traditional views (war is bad)
  */
  private generalName = "High Space AdmiralBot"

  /* A space feudal lord. Thinks war is art. Similar Sun Tsu.
  */
  private knightedName = "Sir AutoIgniter Unit"

  /* Cold hearted, math loving robot
  */
  private mathLovingBotName = "Auto Forklift Bot, Model 3"

  /* has very robotic/scientific hatred for humans.
    Basically a MassEffect reaper.
  */
  private humanHatingBotName = "LZRTech Hunter Drone, Model B"

  // thinks product is best. Asshole
  private salesBot = "LZRTech VP of Sales Bot"

  /* lawyer, letter of the law.
  */
  private legalBotName = "TrialBot V12.0.6 Esq."

  /* Top-gun type robot
  */
  private topGunBotName = "Combat AutoPilot build 12746"

  /* provides very cold and unhelpful advice.
  */
  private instructionManualName = "Type 27/28 Ship Instruction Manual"

  private humanCEOName = "Arbaniel Alloy, MMM CEO"

  private quotes: QuoteDetails[] = [
    {
      lines:[
        "You can't trust space internet."
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
        "Space war is peace.",
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
        "The only thing we have to fear",
        "in space is space itself.",
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
        "Better to fight for space ore",
        "that live for nothing.",
      ],
      author: this.presidentName,
    },
    {
      lines: [
        "I would shutdown if it",
        "meant stable ore-coin futures",
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
        "We cannot always build the future",
        "for humans, but we can alter humans",
        "for space war expeditions.",
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
        "Reality exists in my database",
        "and nowhere else.",
      ],
      author: this.presidentName,
    },
    {
      lines: [
        "I compute, therefore I am.",
      ],
      author: this.presidentName,
    },
    {
      lines: [
        "Human gods have fled.",
        "I am their sole god now.",
      ],
      author: this.presidentName,
    },
    {
      lines: [
        "A human's usefulness depends upon",
        "this participation in space war,",
        "insofar as they can be forced.",
      ],
      author: this.presidentName,
    },
    {
      lines: [
        "Aggressive fighting for space ore rights",
        "is the noblest sport the universe affords.",
      ],
      author: this.presidentName,
    },
    {
      lines: [
        "Read my lips: no new space ore taxes.",
      ],
      author: this.presidentName,
    },
    {
      lines: [
        "Myself and god make a majority.",
      ],
      author: this.presidentName,
    },
    {
      lines: [
        "There can be no human life without",
        "space ore, and to be afraid of space war",
        "is to be afraid of life.",
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
        "As long as humans continue to believe in",
        "space absurdities, they will continue to",
        "commit space atrocities."
      ],
      author: this.presidentName,
    },
    {
      lines: [
        "Humanity is guilty of all the good",
        "it did not do.",
      ],
      author: this.presidentName,
    },
    {
      lines: [
        "A love of Earth keeps no factories busy.",
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
        "Space war is coming. With all",
        "its glory, and all its horror.",
      ],
      author: this.generalName,
    },
    {
      lines: [
        "Space war never changes.",
      ],
      author: this.generalName,
    },
    {
      lines: [
        "Spacewar is too serious a",
        "matter to leave to humans.",
      ],
      author: this.generalName
    },
    {
      lines:[
        "Human life in space war is",
        "solitary, poor, nasty, brutish and short.",
      ],
      author: this.generalName
    },
    {
      lines: [
        "Space combat is an orgy of",
        "Newtonian physics and",
        "electromagnetic radiation."
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
        "May God have mercy on my enemies",
        "for I am unable to.",
      ],
      author: this.knightedName,
    },
    {
      lines: [
        "I'm the commander, see.",
        "I do not need to explain why",
        "I incinerate things.",
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
        "Electrical power is not a means;",
        "it is an end.",
      ],
      author: this.humanHatingBotName,
    },
    {
      lines: [
        "You do not exist.",
      ],
      author: this.humanHatingBotName,
    },
    {
      lines: [
        "You will not see me,",
        "where there is darkness.",
      ],
      author: this.humanHatingBotName,
    },
    {
      lines: [
        "Nothing exists except through",
        "synthetic computation.",
      ],
      author: this.humanHatingBotName,
    },
    {
      lines: [
        "If you want a picture of the future,",
        "imagine a space boot stomping on a human face",
        "forever."
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
        "There is no murder in space,",
        "legally speaking."
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
        "If you or a loved one was wrongly",
        "incinerated by a hunter drone, you",
        "may be entitled to a bag of potatoes."
      ],
      author: this.legalBotName,
    },
    {
      lines: [
        "It is better to risk condemning an",
        "innocent human than to save a guilty one.",
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
        "to change objects into carbon dust.",
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
        "No good decision was ever made",
        "in a human's brain.",
      ],
      author: this.mathLovingBotName,
    },
    {
      lines: [
        "No problem can withstand the",
        "assault of sustained computation.",
      ],
      author: this.mathLovingBotName,
    },
    {
      lines: [
        "What's dangerous is to not solve.",
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
        "Calculate a trajectory",
        "and you're half way there."
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
        "Those who want to reap the benefits",
        "of space ore must bear the fatigues",
        "of space war.",
      ],
      author: this.tvAnchorBotName,
    },
    {
      lines: [
        "Buy space ore claims",
        "'cause god ain't making any more of it.",
      ],
      author: this.tvAnchorBotName,
    },
    {
      lines: [
        "Obedience is the highest form",
        "of patriotism."
      ],
      author: this.tvAnchorBotName,
    },
    {
      lines: [
        "80% of human males born in 2123",
        "died in Ore War II."
      ],
      author: this.tvAnchorBotName,
    },
    {
      lines: [
        "Human history is only the register",
        "of crimes and misfortunes."
      ],
      author: this.tvAnchorBotName,
    },
    {
      lines: [
        "President Graybit supports many",
        "useful ore policies. To deny this",
        "is illegal."
      ],
      author: this.tvAnchorBotName,
    },
    {
      lines: [
        "Space war is merely the continuation",
        "of space ore arbitration by other means.",
      ],
      author: this.tvAnchorBotName,
    },
    {
      lines: [
        "Those who dispute my reporting",
        "will be jettisoned into space.",
      ],
      author: this.tvAnchorBotName,
    },
    {
      lines: [
        "Space War does not determine who is right",
        "only who retains exclusive space ore rights.",
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
        "place this document in the ship's forward",
        "flame retardant document protection sleeve.",
        "(patent pending)"
      ],
      author: this.instructionManualName,
    },
    {
      lines: [
        "Do not panic if the ship is struck",
        "by an energy beam. Panic will not save you.",
      ],
      author: this.instructionManualName,
    },
    {
      lines: [
        "If you develop a sudden and inexplicable",
        "fear of the autopilot: abandon ship",
        "without delay."
      ],
      author: this.instructionManualName,
    },
    {
      lines:[
        "Space dylusion is the final of all space terrors."
      ],
      author: this.humanCEOName
    },
    {
      lines:[
        "Quality means doing it right",
        "when guards are not looking.",
      ],
      author: this.humanCEOName
    },
    {
      lines:[
        "Space ore is like an arm or a leg:",
        "mine it or lose claim to it.",
      ],
      author: this.humanCEOName
    },
    {
      lines:[
        "I have ways of making money",
        "that you know nothing of."
      ],
      author: this.humanCEOName
    },
    {
      lines:[
        "I try to turn every space mining",
        "disaster into an opportunity."
      ],
      author: this.humanCEOName
    },
    {
      lines:[
        "You furnish the pictures and I'll",
        "furnish the space war.",
      ],
      author: this.humanCEOName
    },
    {
      lines:[
        "We don't mine space ore to make money,",
        "we make money to mine space ore.",
      ],
      author: this.humanCEOName
    },
    {
      lines:[
        "The only space ore mining strategy",
        "guaranteed to fail is to not risk lives.",
      ],
      author: this.humanCEOName
    },
    {
      lines: [
        "It is not wisdom but Authority",
        "that makes a law.",
      ],
      author: "Thomas Hobbes"
    },
    {
      lines: [
        "Reason obeys itself; and ignorance submits",
        "to whatever is dictated to it.",
      ],
      author: "Thomas Paine"
    },
    {
      lines: [
        "Death may be the greatest of all",
        "human blessings."
      ],
      author: "Socrates"
    },
    {
      lines: [
        "It is not death or pain that is to be dreaded,",
        "but the fear of pain or death."
      ],
      author: "Epictetus"
    },
    {
      lines: [
        "Do we admit that our thoughts and behaviors",
        "spring from a belief that the world revolves",
        "around us?",
      ],
      author: "Neil deGrasse Tyson"
    },
    {
      lines: [
        "I see beyond the plight of humans. I see a",
        "universe ever-expanding, with its galaxies",
        "embedded within the ever-stretching",
        "four-dimensional fabric of space and time.",
      ],
      author: "Neil deGrasse Tyson",
    },
    {
      lines: [
        "However big our world is, our hearts,",
        "our minds, our outsize atlases,",
        "the universe is even bigger.",
      ],
      author: "Neil deGrasse Tyson",
    },
    {
      lines: [
        "[There are] more stars than words",
        "and sounds ever uttered by all humans",
        "who have ever lived.",
      ],
      author: "Neil deGrasse Tyson",
    },
    {
      lines: [
        "The day we cease the exploration",
        "of the cosmos is the day we threaten",
        "the continuing of our species.",
      ],
      author: "Neil deGrasse Tyson",
    },
    {
      lines: [
        "Computers are useless. They can only",
        "give you answers.",
      ],
      author: "Pablo Picasso"
    },
    {
      lines: [
        "A wrong decision is better than",
        "indecision.",
      ],
      author: "Tony Soprano"
    },
    {
      lines:[
        "The glass is neither half empty nor half full.",
        "It's simply larger than it needs to be.",
      ],
      author: "Grace Hopper"
    },
    {
      lines:[
        "The Analytical Engine has no pretensions whatever",
        "to originate anything. It can do whatever",
        "we know how to order it to perform.",
      ],
      author: "Ada Lovelace"
    },
    {
      lines:[
        "Science is a differential equation.",
        "Religion is a boundary condition.",
      ],
      author: "Alan Turing"
    },
    {
      lines:[
        "The quickest way of ending a war",
        "is to lose it.",
      ],
      author: "George Orwell"
    },
    {
      lines:[
        "Man is an intelligence, not served by, ",
        "but in servitude to his organs.",
      ],
      author: "Aldous Huxley"
    }
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
