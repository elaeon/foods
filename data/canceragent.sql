--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

SET search_path = public, pg_catalog;

--
-- Data for Name: disease_canceragent; Type: TABLE DATA; Schema: public; Owner: agmartinez
--

COPY disease_canceragent (id, name, name_es, nivel, type) FROM stdin;
118	Treosulfan	treosulfano	1	compuesto químico
117	Thiotepa	tiotepa	1	compuesto químico
115	Phosphorus-32	fósforo-32	1	radiación
112	Melphalan	melfalán	1	compuesto químico
111	Lindane	lindano	1	compuesto químico
110	Human T-cell lymphotropic virus type 1	Human T-cell lymphotropic virus type 1	1	microorganismos
109	Fission products, including strontium-90	Productos de fisión, incluyendo strontium-90	1	radiación
108	Etoposide with cisplatin and bleomycin	Etoposide with cisplatin and bleomycin	1	compuesto químico
107	Chlorambucil	clorambucil	1	compuesto químico
106	1,3-Butadiene	1,3-Butadiene	1	compuesto químico
105	Busulfan	busulfán	1	compuesto químico
104	Benzene	benceno	1	compuesto químico
103	Radioiodines, including Iodine-131	Radioiodines, including Iodine-131	1	radiación
102	Welding	soldadura	1	radiación
101	ortho-Toluidine	ortho-Toluidine	1	compuesto químico
100	Schistosoma haematobium	Schistosoma haematobium	1	microorganismos
99	2-Naphthylamine	2-Naphthylamine	1	compuesto químico
98	Magenta production	producción de magenta	1	material
96	Chlornaphazine	Chlornaphazine	1	compuesto químico
95	Benzidine	bencidina	1	compuesto químico
94	Auramine production	producción de auramina	1	material
93	4-Aminobiphenyl	4-Aminobiphenyl	1	compuesto químico
91	Phenacetin	Phenacetin	1	compuesto químico
90	Aristolochic acid, plants containing	Aristoloquina acido, plantas con	1	compuesto químico
89	Trichloroethylene	Tricloroetileno	1	compuesto químico
88	Tamoxifen	tamoxifeno	1	compuesto químico
65	Cyclosporine	ciclosporin	1	compuesto químico
86	Human papillomavirus types 59	Virus del papiloma humano tipo 59	1	microorganismos
83	Human papillomavirus types 52	Virus del papiloma humano tipo 52	1	microorganismos
82	Human papillomavirus types 51	Virus del papiloma humano tipo 51	1	microorganismos
80	Human papillomavirus types 39	Virus del papiloma humano tipo 39	1	microorganismos
78	Human papillomavirus types 33	Virus del papiloma humano tipo 33	1	microorganismos
77	Human papillomavirus types 31	Virus del papiloma humano tipo 31	1	microorganismos
75	Human papillomavirus types 16	Virus del papiloma humano tipo 16	1	microorganismos
72	Diethylstilbestrol	Diethylstilbestrol	1	compuesto químico
70	Fluoro-edenite	Fluoro-edenite	1	compuesto químico
69	Erionite	erionita	1	compuesto químico
68	Shale oils	Petróleo de esquisto	1	compuesto químico
66	Methoxsalen plus ultraviolet A	methoxsalen plus ultraviolet A	1	tratamiento
87	Estrogen menopausal therapy	Terapia menopausica con estrógeno	1	tratamiento
64	Coal-tar distillation	destilación de carbón-alquitran	1	material
63	Azathioprine	azathioprine	1	compuesto químico
60	Solar radiation	radiación solar	1	radiación
58	Tobacco smoke, secondhand	humo de tabaco en el ambiente	1	compuesto químico
57	Sulfur mustard	mostaza de azufre	1	compuesto químico
56	Soot	hollín	1	material
52	Painting	la pintura	1	material
49	Iron and steel founding	fundición de hierro y acero	1	material
48	Hematite mining (underground)	mineria de hematita	1	material
47	Engine exhaust, diesel	Escape de motor de disel	1	compuesto químico
46	Coke production	Producción de coca	1	material
45	Coal-tar pitch	brea de alquitran-carbon	1	material
44	Coal gasification	gasificación de carbon	1	compuesto químico
42	Chromium(VI) compounds	compuestos de cromo(VI)	1	compuesto químico
41	Cadmium and cadmium compounds	Cadmio y compuestos de cadmio	1	compuesto químico
39	Beryllium and beryllium compounds	berilio y compuestos de berilio	1	compuesto químico
38	Arsenic and inorganic arsenic compounds	arsenico y compuestos de arsenico inorganico	1	compuesto químico
37	Aluminum production	producción de aluminio	1	material
35	Asbestos (all forms)	todas las formas de asbestos	1	material
32	Radium-226 and its decay products	radio-226 y sus productos decayentes	1	radiación
31	Nickel compounds	compuestos de niquel	1	compuesto químico
30	Leather dust	polvo de cuero	1	material
28	Vinyl chloride	cloruro de vinilo	1	compuesto químico
26	Thorium-232 and its decay products	torio-232 y sus productos decayentes	1	radiación
25	Plutonium	plutonio	1	radiación
24	Opisthorchis viverrini	Opisthorchis viverrini	1	microorganismos
23	Hepatitis C virus	virus de la hepatitis C	1	microorganismos
20	1,2-Dichloropropane	1,2-Dichloropropane	1	compuesto químico
19	Clonorchis sinensis	Clonorchis sinensis	1	microorganismos
9	Formaldehyde	formaldehyde	1	compuesto químico
16	Processed meat (consumption of)	consumo de carne procesada	1	alimento
15	X-radiation, gamma-radiation	Rayos X, rayos gama	1	radiación
13	Helicobacter pylori	Helicobacter pylori	1	microorganismos
11	Wood dust	aserrin	1	material
10	Salted fish, Chinese-style	pescado salado, estilo chino	1	alimento
8	Epstein-Barr virus	virus Epstein-Barr	1	microorganismos
18	Aflatoxins	aflatoxins	1	compuesto químico
5	Tobacco, smokeless	tabaco	1	material
3	Betel quid without tobacco	betel quid sin tabaco	1	material
2	Betel quid with tobacco	betel quid con tabaco	1	material
119	2,3,7,8-Tetrachlorodibenzo-para-dio	2,3,7,8-Tetrachlorodibenzo-para-dio	1	compuesto químico
17	Human immunodeficiency virus type 1	virus de inmunodeficiencia humana tipo 1	1	microorganismos
14	Rubber production industry	producción industrial de caucho	1	material
12	Acetaldehyde associated with consumption of alcoholic beverages	acetaldehído asociado con el consumo de alcohol	1	compuesto químico
6	Tobacco smoking	Fumar tabaco	1	material
116	Semustine (methyl-CCNU)	Semustine (methyl-CCNU)	1	compuesto químico
113	MOPP (vincristine-prednisone-nitrogenmustard-procarbazine mixture)	MOPP (vincristine-prednisone-nitrogenmustard-procarbazine mixture)	1	compuesto químico
97	Cyclophosphamide	Cyclophosphamide	1	compuesto químico
92	Phenacetin, analgesic mixtures containing	Phenacetin, mezclas de analgésicos con	1	compuesto químico
85	Human papillomavirus types 58	Virus del papiloma humano tipo 58	1	microorganismos
84	Human papillomavirus types 56	Virus del papiloma humano tipo 56	1	microorganismos
81	Human papillomavirus types 45	Virus del papiloma humano tipo 45	1	microorganismos
79	Human papillomavirus types 35	Virus del papiloma humano tipo 35	1	microorganismos
76	Human papillomavirus types 18	Virus del papiloma humano tipo 18	1	microorganismos
74	Diethylstilbestrol (exposure in utero)	Diethylstilbestrol (exposure in utero)	1	compuesto químico
71	Kaposi sarcoma herpes virus	Kaposi sarcoma virus de herpes	1	microorganismos
67	Mineral oils,  untreated or mildly treated	Aceites minerales, no tratados o medianamente	1	compuesto químico
73	Estrogen-progestogen menopausal therapy	Terapia menopausica con estrógeno-progestogen	1	tratamiento
62	Polychlorinated biphenyls	bifenilos policlorados	1	compuesto químico
61	Ultraviolet-emitting tanning devices	aparatos de bronceados emisores de luz ultravioleta	1	radiación
59	Radium-224 and its decay products	radio-224 y sus productos decayentes	1	radiación
55	Silica dust, crystalline	polvo de sílice cristalina	1	material
54	Radon-222 and its decay products	radon-222 y sus productos decayentes	1	radiación
53	Particulate matter in outdoor air pollution	Partículas suspendidas en la contaminación del aire	1	compuesto químico
51	Outdoor air pollution	contaminación del aire	1	compuesto químico
1	Alcoholic beverages	bebidas alcoholicas	1	alimento
43	Coal,  indoor emissions from household combustion	emisiones en la combustion de carbon en interiores	1	compuesto químico
40	Bis(chloromethyl)ether; chloromethyl methyl ether (technical grade)	Bis(chloromethyl)ether; chloromethyl methyl ether (technical grade)	1	compuesto químico
36	Acheson process, occupational exposures associated with	exposición ocupacional asociado con la producción de acheson	1	material
34	Acid mists, strong inorganic	vapores de acido, inorganico y fuerte	1	compuesto químico
33	Radium-228 and its decay products	radio-228 y sus productos decayentes	1	radiación
29	Isopropyl alcohol production	producción de alcohol isopropílico	1	material
27	Tobacco smoking (in smokers and in smokers’ children)	fumar tabaco (en fumadores e hijos de fumadores)	1	compuesto químico
22	Hepatitis B virus	virus de la hepatitis B	1	microorganismos
21	Estrogen-progestogen contraceptives	anticonceptivos de estrogeno-progestogen	1	compuesto químico
\.


--
-- Name: disease_canceragent_id_seq; Type: SEQUENCE SET; Schema: public; Owner: agmartinez
--

SELECT pg_catalog.setval('disease_canceragent_id_seq', 119, true);


--
-- PostgreSQL database dump complete
--

