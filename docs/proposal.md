# Identified, Yet Excluded? Digital Identification and the Right to Social Protection for Marginalised Groups: Cross-Country Evidence

*Research proposal · @Hanz · 4 October 2026. Text as supplied by the author; tables reformatted for Markdown. The analysis decisions that implement this proposal are in `docs/analysis_plan.md`.*

## Abstract

Governments across the Global South are rebuilding their welfare systems around digital identification. Supporters argue that biometric and digital ID helps cash transfers reach the people they are meant for, faster and with less leakage. Human rights scholars and UN mandate-holders have warned that the same systems can remove people from the welfare state. The people most at risk are women, the rural poor, older people, persons with disabilities and anyone who cannot prove who they are. Almost all of the evidence in this debate comes from single-country case studies, India's Aadhaar above all. Whether digital ID widens or narrows access to social protection across countries has not been tested systematically.

This project builds a country-year panel covering roughly 120 low- and middle-income economies between 2014 and 2024. It links the World Bank's ID4D Global Dataset and the Global Findex surveys to ILO data on effective social protection coverage (SDG indicator 1.3.1). It also adds an original, hand-coded record of when each country rolled out its digital ID. With staggered difference-in-differences estimators, the study asks two questions: does digital ID change coverage, and for whom? The central hypothesis is conditional. Digital ID expands coverage where legal and institutional safeguards are in place, and deepens exclusion where they are absent. Viet Nam, Cambodia and Lao PDR are discussed as illustrative cases at three different stages of digitalisation. The study contributes to the literature on the digital welfare state and to the monitoring of SDG targets 1.3 and 16.9. It also gives development agencies evidence on how rights safeguards should be sequenced with ID rollout.

**Keywords:** digital identification; social protection; digital welfare state; legal identity; SDG 16.9; administrative burden; staggered difference-in-differences

## 1. Introduction and problem statement

Social protection is a human right. Article 22 of the Universal Declaration of Human Rights and Article 9 of the International Covenant on Economic, Social and Cultural Rights say so. Yet for most of the world's poor, that right depends on something more mundane: being able to prove who you are. The World Bank's ID4D initiative estimates that around 800 million people still lack an official form of identification (ID4D, 2025). Over half of them are children whose births were never registered. The ILO reports that just over half of the world's population is covered by at least one social protection benefit, which leaves billions without any coverage at all (ILO, 2024).

Digital identification has been promoted as the bridge between these two gaps. Over the past decade, development agencies, donors and national governments have backed foundational ID systems that are biometric, centralised and increasingly linked to bank accounts, mobile money and social registries. The promise is a welfare state that can see everyone it is meant to serve. Payments would reach beneficiaries directly, duplicate and "ghost" recipients would be removed, and enrolment would become simple enough for people who were previously invisible to the state (Gelb & Metz, 2018).

A second body of work tells a darker story. In his 2019 report to the UN General Assembly, the Special Rapporteur on extreme poverty and human rights described the rise of a "digital welfare state". In such a state, automation and digital ID are used to cut costs, target and police claimants, and shift the burden of proof onto the poor (Alston, 2019). The Center for Human Rights and Global Justice at NYU went further. It concluded that the benefits claimed for the dominant model of digital ID "have not been convincingly proven", and that the model may be causing serious harm (CHRGJ, 2022). In India, authentication failures under Aadhaar have been linked to people being denied food rations and pensions (Khera, 2019; Muralidharan et al., 2020).

The two camps rarely meet on the same evidence. Optimists cite programme-level gains in efficiency. Critics document exclusion through careful but country-specific qualitative work. Neither side has asked the comparative question that matters most for policy: across countries, does introducing digital ID raise or lower the share of vulnerable people who actually receive social protection, and under what conditions? This proposal sets out to answer it.

## 2. State of the art and research gap

The literature falls into three strands. Each answers part of the question, and none answers all of it.

**Programme evaluations.** The strongest causal evidence comes from India. Muralidharan, Niehaus and Sukhtankar (2016) found that biometric smartcards in Andhra Pradesh made welfare payments faster and less leaky without lowering programme access. Their later experiment in Jharkhand, however, found that mandatory biometric authentication for food rations raised transaction costs for beneficiaries and excluded some genuine claimants without saving money (Muralidharan et al., 2020). These studies are rigorous, but they are internally valid for one state, one programme and one technology. They cannot tell us whether the effect holds in Kenya, Peru or Viet Nam.

**Critical and human rights scholarship.** A growing body of work in information systems, development studies and critical data studies treats digital ID as a form of state power, not a neutral tool. Masiero and Das (2019) show how "datafying" anti-poverty programmes can turn data problems into problems of entitlement. Weitzberg et al. (2021) describe digital identity in aid as caught "between surveillance and recognition". Eubanks (2018) documents how automated eligibility systems in the United States punish the poor. This work is rich in mechanisms but relies mostly on case studies. It has not yet produced cross-national estimates.

**Global monitoring.** The World Bank's ID4D and Global Findex data, and the ILO's World Social Protection Database, now provide cross-country measures of ID ownership, account ownership, receipt of government transfers and effective coverage. They are used mainly for description: tracking how many people have an ID or a benefit. They are rarely joined together, and almost never used to estimate how ID systems affect welfare outcomes.

The gap is therefore threefold:

1. **Empirical.** No published study, to the author's knowledge, estimates the effect of digital ID rollout on social protection coverage across a large panel of countries.
2. **Distributional.** Existing global figures report averages. They do not show whether the gains go to people who were already easy to reach while the hardest-to-reach fall further behind.
3. **Conditional.** The critical literature implies that harm depends on context: data protection, accountability and the space for civil society to challenge errors. This conditional claim has never been tested quantitatively.

A systematic search of Scopus and Web of Science will be carried out in the first month to confirm this gap (see Section 9).

## 3. Conceptual framework and hypotheses

The study brings together two ideas that are usually discussed apart. The first is legibility. States can only distribute what they can see, and they make populations visible by standardising, registering and counting them (Scott, 1998). Digital ID is the most powerful legibility technology yet built. The second is administrative burden: the learning, compliance and psychological costs people face when they deal with the state (Herd & Moynihan, 2018). Burdens are never neutral. They fall hardest on those with the least time, literacy, money and mobility.

Taken together, these ideas suggest that digital ID works through two opposing channels.

- **An inclusion channel.** A unique, verifiable identity lowers the state's cost of finding and paying eligible people. It makes portable, direct-to-account payments possible and reduces leakage to intermediaries. Coverage should rise.
- **An exclusion channel.** The same system makes the ID a gate. People without the credential, or whose fingerprints, documents or data do not match, can be refused. The burden of fixing errors moves from the state to the claimant. Coverage among the hardest-to-reach should fall, or rise more slowly than among everyone else.

Which channel dominates is not a technical question. It depends on whether claimants can contest errors, whether alternatives to biometric authentication are allowed, and whether personal data is protected by law. I call these conditions rights safeguards. The framework yields four hypotheses:

- **H1 (average effect).** Digital ID rollout is associated with higher effective social protection coverage on average.
- **H2 (distributional effect).** The gain is smaller for women, the poorest 40 per cent and rural residents. Within-country coverage gaps therefore widen after rollout.
- **H3 (conditional effect).** Rollout is associated with larger gains and narrower gaps where rights safeguards are stronger. Safeguards are proxied by a data protection law, government accountability and civil society space.
- **H4 (design effect).** Systems that make biometric authentication mandatory for receiving benefits show weaker inclusion effects than systems that allow non-biometric alternatives.

The net effect on the hardest-to-reach depends on which channel dominates. The framework predicts that safeguards decide this.

## 4. Research questions and objectives

The overarching question is: under what conditions does digital identification expand, rather than restrict, access to social protection for marginalised groups?

- **RQ1.** What is the average association between digital ID rollout and effective social protection coverage across low- and middle-income countries?
- **RQ2.** How is this association distributed across groups defined by gender, income, rural residence and age? Do within-country gaps narrow or widen?
- **RQ3.** How do rights safeguards and system design moderate the effect?

Objectives:

1. Build and publish an open, documented dataset recording the year each country introduced a digital foundational ID and the main design features of that system.
2. Estimate the average and group-specific effects of digital ID on social protection outcomes with estimators robust to staggered adoption.
3. Test whether rights safeguards condition these effects.
4. Translate the findings into recommendations for national governments and for agencies financing ID systems, with a short comparative discussion of Viet Nam, Cambodia and Lao PDR.

## 5. Data and measurement

The study uses only secondary data that are publicly available or free on registration. The unit of analysis is the country-year (2014–2024). The Findex survey waves (2014, 2017, 2021, 2024) also allow a country-wave panel disaggregated by population group.

| Construct | Indicator | Source | Coverage |
|---|---|---|---|
| Outcome: effective coverage | Share of population covered by at least one social protection benefit (SDG 1.3.1), total and by group (older persons, children, persons with severe disabilities, vulnerable persons) | ILO World Social Protection Database / ILOSTAT | Global, irregular years |
| Outcome: benefit receipt | Share of adults who received a government transfer or pension in the past year, by sex, income quintile and residence | Global Findex 2025 and earlier waves | About 140 economies, 2014–2024 |
| Treatment: ID access | Foundational ID ownership, by sex, income, education and residence | ID4D Global Dataset | 175 countries, 2016–2025 |
| Treatment: digital ID rollout | Year a digital or biometric foundational ID began national enrolment; design features (biometric authentication, mandatory link to benefits) | Hand-coded by the author from legislation, ID agency reports, ID4D diagnostics and news archives | Target: all LMICs |
| Moderator: data protection | Existence and year of a national data protection law | UNCTAD Data Protection and Privacy Legislation Worldwide | Global |
| Moderator: accountability | Voice and Accountability; Rule of Law | Worldwide Governance Indicators | Global, annual |
| Moderator: civic space | Civil society participation and repression indices | V-Dem | Global, annual |
| Controls | GDP per capita, social protection spending (% of GDP), mobile phone and account penetration, urbanisation, conflict | World Development Indicators, ILO, Findex, UCDP | Global |

Two points need care. First, SDG 1.3.1 is reported irregularly and has gaps for many countries. The Findex measure of transfer receipt therefore serves as the primary outcome for the group-level analysis, and SDG 1.3.1 as the primary outcome for the aggregate analysis. Second, the treatment variable is the project's original contribution. Each rollout date will be coded from at least two independent sources and checked by a second coder on a random 20 per cent sample, with inter-coder agreement reported. H4 depends on design information that may be incomplete for some countries and is treated as exploratory.

## 6. Empirical strategy

Countries introduced digital ID in different years. This staggered timing is the basis of identification: countries that adopted later serve as controls for those that adopted earlier. Recent econometric work shows that conventional two-way fixed effects regressions can be badly biased when adoption is staggered and effects vary over time (Goodman-Bacon, 2021). The main estimates will therefore use the group-time average treatment effects of Callaway and Sant'Anna (2021):

ATT(g,t) = E[Y_t − Y_{g−1} | G = g] − E[Y_t − Y_{g−1} | D_t = 0, G ≠ g]

Here g is the year a country adopted digital ID, t is the calendar year, and Y is the coverage outcome. Comparison units are countries not yet treated by year t. Group-time effects are aggregated into an event-study profile, which allows a visual check of pre-trends before rollout. Results will be compared with the estimators of Sun and Abraham (2021) and de Chaisemartin and D'Haultfœuille (2020).

**Distributional effects (RQ2).** The outcome is replaced by the within-country gap in benefit receipt: men minus women, richest 60 per cent minus poorest 40 per cent, and urban minus rural.

**Conditional effects (RQ3).** The sample is split by safeguard strength at the time of rollout, and the analysis is repeated with a continuous interaction term in a two-way fixed effects specification for comparison:

Y_it = α_i + λ_t + β·DigitalID_it + γ·(DigitalID_it × Safeguard_i) + X_it′δ + ε_it

**Threats to validity.** Rollout is not random. Countries may adopt digital ID at the same moment they expand social programmes, often with the same donor money. Four steps address this. First, the analysis controls for social protection spending and donor-financed ID projects. Second, it checks for pre-trends in the event study. Third, it runs placebo tests on outcomes that digital ID should not affect. Fourth, it applies sensitivity analysis for violations of parallel trends (Rambachan & Roth, 2023). The results will be framed as robust conditional associations, not as definitive causal effects. Because a single-country study cannot show heterogeneity across institutional settings, the cross-country design is a strength, not a compromise.

**Illustrative cases.** Viet Nam (chip-based citizen ID and the VNeID platform, with social assistance moving to bank accounts), Cambodia (IDPoor on-demand registration and cashless Family Package payments) and Lao PDR (an early-stage system with effective coverage reported at 15.5 per cent in 2021) are placed on the estimated event-study profile. The discussion uses policy documents to interpret where each country sits.

## 7. Expected contributions and policy relevance

- **To the digital welfare state debate.** It gives the first cross-national quantitative test of a claim that has so far rested on case studies. Whatever the sign of the result, the debate moves forward. A positive and conditional effect would show that the critics' concerns are about governance, not technology. A null or negative effect among the poorest would put real numbers behind the warnings of UN mandate-holders.
- **To the measurement of exclusion.** Shifting attention from average coverage to within-country gaps makes visible the people that headline SDG figures hide. This is the practical meaning of the 2030 Agenda's promise to "leave no one behind".
- **To policy sequencing.** If safeguards condition the effect, the policy lesson is concrete. Data protection law, grievance redress and non-biometric fallbacks should come before a digital ID is made a condition for receiving benefits, not after. This message is relevant to the World Bank, regional development banks and bilateral donors that finance ID systems, and to governments such as Viet Nam's that are linking social assistance to digital platforms.
- **A public good.** The hand-coded rollout dataset will be released openly with full documentation, so that other researchers can reuse and extend it.

The study speaks directly to SDG 1.3 (social protection systems for all), SDG 10.2 (social, economic and political inclusion) and SDG 16.9 (legal identity for all).

## 8. Ethics, limitations and risk management

The study uses only anonymised, aggregate or publicly released survey data. No human participants are contacted and no personal data are processed, so the ethical risk is low. All data will be handled under the licence terms of the providers. Code and the rollout dataset will be deposited in an open repository (for example Zenodo or the Harvard Dataverse), in line with the FAIR principles.

| Risk | Likelihood | Mitigation |
|---|---|---|
| Sparse or irregular SDG 1.3.1 series | High | Use Findex transfer receipt as the main group-level outcome; use multiple imputation only as a robustness check |
| Ambiguous rollout dates | Medium | Clear coding rules, two sources per date, second coder on a 20% sample, sensitivity tests with alternative dates |
| Endogenous adoption | Medium | Staggered DiD with not-yet-treated controls, pre-trend tests, placebo outcomes, Rambachan–Roth sensitivity bounds |
| Too few treated countries in some subgroups | Medium | Pool regions, report wild-cluster bootstrap inference, present subgroup results as exploratory |
| A similar study is published during the project | Low | Monthly literature alert; the open dataset and the safeguard analysis remain distinct contributions |

The main limitation is that country-level data cannot follow individuals as they gain or lose access. The findings will describe patterns across systems, not the experience of particular claimants. The concluding section will point to the qualitative literature that documents those experiences, and to where future primary research is most needed.

## 9. Work plan and timeline

The project runs for twelve months. The two gates mark the points where the co-author's input shapes the work: first on the design, then on the results. The dataset phase is the longest because hand-coding rollout dates is the project's original contribution and the main source of risk.

*[The timeline chart was not included in the text supplied.]*

## 10. Dissemination and target journals

The primary output is one article for a peer-reviewed journal ranked Q1 in Scopus/SJR. The final choice of journal depends on whether the main finding is methodological or substantive. Candidate journals (rankings to be re-checked on SJR before submission):

| Journal | Why it fits |
|---|---|
| World Development | Cross-country development evidence with a clear policy message |
| Government Information Quarterly | Digital government, ID systems and public value |
| Global Social Policy | Comparative social protection and international organisations |
| Information Technology for Development | ICT4D, digital ID and inclusion |

Secondary outputs: a working paper posted to SSRN before submission; the open rollout dataset with a short data note; a two-page policy brief in English and Vietnamese; a presentation at an international conference, such as the Development Studies Association or the IFIP 9.4 conference on ICT4D.

## References

Alston, P. (2019). *Report of the Special Rapporteur on extreme poverty and human rights* (A/74/493). United Nations General Assembly.

Callaway, B., & Sant'Anna, P. H. C. (2021). Difference-in-differences with multiple time periods. *Journal of Econometrics, 225*(2), 200–230.

Center for Human Rights and Global Justice. (2022). *Paving a digital road to hell? A primer on the role of the World Bank and global networks in promoting digital ID*. New York University School of Law. https://chrgj.org/2022-06-paving-digital-road-to-hell/

de Chaisemartin, C., & D'Haultfœuille, X. (2020). Two-way fixed effects estimators with heterogeneous treatment effects. *American Economic Review, 110*(9), 2964–2996.

Eubanks, V. (2018). *Automating inequality: How high-tech tools profile, police, and punish the poor*. St. Martin's Press.

Gelb, A., & Metz, A. D. (2018). *Identification revolution: Can digital ID be harnessed for development?* Center for Global Development / Brookings Institution Press.

Goodman-Bacon, A. (2021). Difference-in-differences with variation in treatment timing. *Journal of Econometrics, 225*(2), 254–277.

Herd, P., & Moynihan, D. P. (2018). *Administrative burden: Policymaking by other means*. Russell Sage Foundation.

International Labour Organization. (2024). *World social protection report 2024–26: Universal social protection for climate action and a just transition*. ILO.

Kaufmann, D., Kraay, A., & Mastruzzi, M. (2011). The Worldwide Governance Indicators: Methodology and analytical issues. *Hague Journal on the Rule of Law, 3*(2), 220–246.

Khera, R. (Ed.). (2019). *Dissent on Aadhaar: Big data meets big brother*. Orient BlackSwan.

Masiero, S., & Das, S. (2019). Datafying anti-poverty programmes: Implications for data justice. *Information, Communication & Society, 22*(7), 916–933.

Muralidharan, K., Niehaus, P., & Sukhtankar, S. (2016). Building state capacity: Evidence from biometric smartcards in India. *American Economic Review, 106*(10), 2895–2929.

Muralidharan, K., Niehaus, P., & Sukhtankar, S. (2020). *Identity verification standards in welfare programs: Experimental evidence from India* (NBER Working Paper No. 26744). National Bureau of Economic Research.

Rambachan, A., & Roth, J. (2023). A more credible approach to parallel trends. *Review of Economic Studies, 90*(5), 2555–2591.

Scott, J. C. (1998). *Seeing like a state: How certain schemes to improve the human condition have failed*. Yale University Press.

Sun, L., & Abraham, S. (2021). Estimating dynamic treatment effects in event studies with heterogeneous treatment effects. *Journal of Econometrics, 225*(2), 175–199.

Weitzberg, K., Cheesman, M., Martin, A., & Schoemaker, E. (2021). Between surveillance and recognition: Rethinking digital identity in aid. *Big Data & Society, 8*(1).

World Bank. (2025). *The Global Findex Database 2025*. https://microdata.worldbank.org/index.php/catalog/7860

World Bank ID4D. (2025). *ID4D Global Dataset*. https://id4d.worldbank.org/global-dataset
