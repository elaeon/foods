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
-- Data for Name: disease_cancer; Type: TABLE DATA; Schema: public; Owner: agmartinez
--

COPY disease_cancer (id, name, organ, name_es) FROM stdin;
39	All cancer sites (combined)	todos	Cáncer en todo el cuerpo
10	Anus		Ano
17	Bone		Hueso
35	Brain and central nervous system		Cerebro y sistema nervioso central
22	Breast		Pecho (Mama)
9	Colon and rectum		Colón y recto
6	Digestive tract, upper		Tracto digestivo superior
27	Endometrium	aparato reproductivo	Endometrio
21	Endothelium (Kaposi sarcoma)	sistema circulatorio	Endotelio
34	Eye		Ojo
12	Gall bladder	digestivo	Vesícula biliar
30	Kidney		Riñon
15	Larynx		Laringe
37	Leukaemia and/or lymphoma		Leucemia o linfoma
11	Liver and bile duct		Hígado y ducto viliar
16	Lung		Pulmón
20	Mesothelium (pleura and peritoneum)		Mesotelio (pleura and peritoneum)
38	Multiple sites (unspecified)		Varios sitios no especificos
14	Nasal cavity and paranasal sinus		Cavidad nasal y senos paranasales
5	Nasopharynx		Nasofaringe
7	Oesophagus		Esófago
1	Oral cavity		Cavidad oral
28	Ovary		Ovario
13	Pancreas		Páncreas
29	Penis		Pene
4	Pharynx		Faringe
32	Renal pelvis and ureter		Pelvis renal y uretra
2	Salivary gland		Glándula salivaria
18	Skin (melanoma)		Piel (melanoma)
19	Skin (other malignant neoplasms)		Piel (otros neoplasmas malignos)
8	Stomach		Estómago
36	Thyroid		Tiróides
3	Tonsil		Amígdala palatina
33	Urinary bladder		Vejiga urinaria
25	Uterine cervix		Cervix uterino
24	Vagina		Vagina
23	Vulva	aparato reproductivo	Vulva
\.


--
-- Data for Name: disease_cancer5yrsurvivalrate; Type: TABLE DATA; Schema: public; Owner: agmartinez
--

COPY disease_cancer5yrsurvivalrate (id, period, percentaje, cancer_id) FROM stdin;
1	2005-2011	69	39
2	2005-2011	35	35
3	2005-2011	91	22
4	2005-2011	66	9
5	2005-2011	74	30
6	2005-2011	63	15
7	2005-2011	62	37
8	2005-2011	18	11
9	2005-2011	18	16
10	2005-2011	93	18
11	2005-2011	66	1
12	2005-2011	66	4
13	2005-2011	46	28
14	2005-2011	8	13
15	2005-2011	30	8
16	2005-2011	98	36
17	2005-2011	79	33
18	2005-2011	69	25
\.


--
-- Name: disease_cancer5yrsurvivalrate_id_seq; Type: SEQUENCE SET; Schema: public; Owner: agmartinez
--

SELECT pg_catalog.setval('disease_cancer5yrsurvivalrate_id_seq', 18, true);


--
-- Name: disease_cancer_id_seq; Type: SEQUENCE SET; Schema: public; Owner: agmartinez
--

SELECT pg_catalog.setval('disease_cancer_id_seq', 39, true);


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
43	Coal,  indoor emissions from household combustion	emisiones en la combustion de carbon en interiores	1	compuesto químico
40	Bis(chloromethyl)ether; chloromethyl methyl ether (technical grade)	Bis(chloromethyl)ether; chloromethyl methyl ether (technical grade)	1	compuesto químico
36	Acheson process, occupational exposures associated with	exposición ocupacional asociado con la producción de acheson	1	material
34	Acid mists, strong inorganic	vapores de acido, inorganico y fuerte	1	compuesto químico
33	Radium-228 and its decay products	radio-228 y sus productos decayentes	1	radiación
29	Isopropyl alcohol production	producción de alcohol isopropílico	1	material
27	Tobacco smoking (in smokers and in smokers’ children)	fumar tabaco (en fumadores e hijos de fumadores)	1	compuesto químico
22	Hepatitis B virus	virus de la hepatitis B	1	microorganismos
21	Estrogen-progestogen contraceptives	anticonceptivos de estrogeno-progestogen	1	compuesto químico
1	Alcoholic beverages	bebidas alcohólicas	1	alimento
\.


--
-- Name: disease_canceragent_id_seq; Type: SEQUENCE SET; Schema: public; Owner: agmartinez
--

SELECT pg_catalog.setval('disease_canceragent_id_seq', 119, true);


--
-- Data for Name: disease_canceragentrelation; Type: TABLE DATA; Schema: public; Owner: agmartinez
--

COPY disease_canceragentrelation (id, agent_id, cancer_id) FROM stdin;
1	1	1
2	2	1
3	3	1
5	5	1
6	6	1
9	1	4
10	2	4
12	6	4
13	8	5
14	9	5
15	10	5
16	6	5
17	11	5
18	12	6
19	12	7
20	1	7
21	2	7
22	3	7
23	5	7
24	6	7
26	13	8
27	14	8
28	6	8
29	15	8
30	1	9
31	6	9
32	15	9
33	16	9
34	17	10
36	18	11
37	1	11
38	19	11
39	20	11
40	21	11
41	22	11
42	23	11
43	24	11
44	25	11
45	26	11
46	27	11
47	28	11
48	26	12
49	5	13
50	6	13
51	29	14
52	30	14
53	31	14
54	32	14
55	33	14
56	6	14
57	11	14
58	34	15
59	1	15
60	35	15
61	6	15
62	36	16
63	37	16
64	38	16
65	35	16
66	39	16
67	40	16
68	41	16
69	42	16
70	43	16
71	44	16
72	45	16
73	46	16
74	47	16
75	48	16
76	49	16
78	31	16
79	51	16
80	52	16
81	53	16
82	25	16
83	54	16
84	14	16
85	55	16
86	56	16
87	57	16
88	58	16
89	6	16
91	25	17
92	59	17
93	32	17
94	33	17
95	15	17
96	60	18
97	61	18
98	62	18
99	38	19
100	63	19
101	64	19
102	45	19
103	65	19
104	66	19
105	67	19
106	68	19
107	60	19
108	56	19
109	15	19
110	35	20
111	69	20
112	70	20
113	52	20
114	17	21
115	71	21
116	1	22
117	72	22
118	21	22
119	73	22
120	15	22
122	74	24
124	74	25
125	21	25
126	17	25
127	75	25
128	76	25
129	77	25
130	78	25
131	79	25
132	80	25
133	81	25
134	82	25
135	83	25
136	84	25
137	85	25
138	86	25
139	6	25
141	73	27
142	88	27
143	35	28
144	87	28
145	6	28
147	6	30
149	89	30
151	91	32
152	92	32
153	6	32
154	37	33
155	93	33
156	38	33
157	94	33
158	95	33
159	96	33
160	97	33
161	98	33
162	99	33
163	52	33
164	14	33
165	100	33
166	6	33
167	101	33
168	15	33
169	17	34
170	61	34
171	102	34
172	15	35
173	103	36
174	15	36
175	63	37
176	104	37
177	105	37
178	106	37
179	107	37
180	97	37
181	65	37
182	8	37
183	108	37
184	109	37
185	9	37
186	13	37
187	23	37
188	17	37
189	110	37
190	71	37
191	111	37
192	112	37
193	113	37
195	115	37
196	14	37
197	116	37
198	117	37
199	26	37
200	6	37
201	118	37
202	15	37
203	65	38
204	109	38
25	15	7
90	15	16
150	90	32
194	113	37
4	75	1
8	75	3
11	75	4
35	75	10
121	75	23
123	75	24
146	75	29
140	87	27
205	15	38
206	119	39
7	15	2
148	15	30
207	6	11
77	113	16
\.


--
-- Name: disease_canceragentrelation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: agmartinez
--

SELECT pg_catalog.setval('disease_canceragentrelation_id_seq', 207, true);


--
-- Data for Name: disease_causamortality; Type: TABLE DATA; Schema: public; Owner: agmartinez
--

COPY disease_causamortality (id, description, cie_10) FROM stdin;
1	Diabetes mellitus	E10-E14
2	Enfermedades isquémicas del corazón	I20-I25
3	Enfermedad cerebrovascular	I60-I69
4	Cirrosis y otras enfermedades crónicas del hígado	K70, 72.1, 73, 74, 76
5	Enfermedad pulmonar obstructiva crónica	J40-J44, J67
6	Agresiones (homicidios)	X85-Y09, Y87.1
7	Enfermedades hipertensivas	I10-I15
8	Infecciones respiratorias agudas bajas	J09-J18, J20-J22
9	Accidentes de transporte	CIE-10
10	Nefritis y nefrosis	N00-N19
11	Ciertas afecciones originadas en periodo perinatal	P00-P96
12	Desnutrición calórico protéica	E40-E46
13	Tumor maligno de tráquea, bronquios y pulmón	C33-C34
14	Lesiones autoinfligidas intencionalmente (suicidios)	X60-X84, Y87.0
15	Tumor maligno de la próstata	C61
16	Tumor maligno del hígado	C22
17	Tumor maligno del estómago	C16
18	Tumor maligno de la mama	C50
19	VIH/SIDA	B20-B24
20	Tumor maligno del cuello del útero	C53
\.


--
-- Name: disease_causamortality_id_seq; Type: SEQUENCE SET; Schema: public; Owner: agmartinez
--

SELECT pg_catalog.setval('disease_causamortality_id_seq', 20, true);


--
-- Data for Name: disease_mortalityyears; Type: TABLE DATA; Schema: public; Owner: agmartinez
--

COPY disease_mortalityyears (id, year, amount, causa_mortality_id) FROM stdin;
1	2013	87245	1
2	2012	85055	1
3	2011	80788	1
4	2010	82964	1
5	2009	77699	1
6	2008	75637	1
7	2007	70517	1
8	2006	68421	1
9	2005	67159	1
10	2004	62243	1
11	2003	59192	1
12	2002	54925	1
13	2001	49954	1
14	2000	46614	1
15	2013	77285	2
16	2012	74057	2
17	2011	71072	2
18	2010	70888	2
19	2009	63332	2
20	2008	59579	2
21	2007	55794	2
22	2006	53619	2
23	2005	53188	2
24	2004	50461	2
25	2003	50757	2
26	2002	48285	2
27	2001	45421	2
28	2000	43753	2
29	2013	31999	3
30	2012	31905	3
31	2011	31235	3
32	2010	32306	3
33	2009	30943	3
34	2008	30212	3
35	2007	29240	3
36	2006	27350	3
37	2005	27370	3
38	2004	26975	3
39	2003	26849	3
40	2002	26526	3
41	2001	25657	3
42	2000	25357	3
43	2013	29335	4
44	2012	28904	4
45	2011	28392	4
46	2010	28369	4
47	2009	28309	4
48	2008	28422	4
49	2007	27829	4
50	2006	26715	4
51	2005	27566	4
52	2004	26867	4
53	2003	26821	4
54	2002	26142	4
55	2001	25704	4
56	2000	25378	4
57	2013	24068	5
58	2012	22433	5
59	2011	22595	5
60	2010	23797	5
61	2009	21716	5
62	2008	20565	5
63	2007	19710	5
64	2006	19182	5
65	2005	20253	5
66	2004	18806	5
67	2003	18117	5
68	2002	16851	5
69	2001	15944	5
70	2000	15915	5
71	2013	23063	6
72	2012	25967	6
73	2011	27213	6
74	2010	25757	6
75	2009	19804	6
76	2008	13900	6
77	2007	8814	6
78	2006	10371	6
79	2005	9852	6
80	2004	9252	6
81	2003	9989	6
82	2002	9975	6
83	2001	10166	6
84	2000	10638	6
85	2013	19488	7
86	2012	19161	7
87	2011	18942	7
88	2010	17695	7
89	2009	18167	7
90	2008	15694	7
91	2007	14565	7
92	2006	12894	7
93	2005	12876	7
94	2004	12203	7
95	2003	11330	7
96	2002	10696	7
97	2001	10170	7
98	2000	9747	7
99	2013	18350	8
100	2012	17055	8
101	2011	16401	8
102	2010	17131	8
103	2009	18754	8
104	2008	15096	8
105	2007	14589	8
106	2006	15180	8
107	2005	14979	8
108	2004	14215	8
109	2003	13738	8
110	2002	13662	8
111	2001	13101	8
112	2000	14213	8
113	2013	16763	9
114	2012	17726	9
115	2011	17225	9
116	2010	17098	9
117	2009	18402	9
118	2008	17585	9
119	2007	15807	9
120	2006	17454	9
121	2005	16682	9
122	2004	15728	9
123	2003	15552	9
124	2002	15222	9
125	2001	14629	9
126	2000	14708	9
127	2013	14803	10
128	2012	14452	10
129	2011	13858	10
130	2010	13483	10
131	2009	13120	10
132	2008	12592	10
133	2007	11726	10
134	2006	11639	10
135	2005	11397	10
136	2004	10774	10
137	2003	10490	10
138	2002	10054	10
139	2001	10477	10
140	2000	9782	10
141	2013	12935	11
142	2012	14391	11
143	2011	14825	11
144	2010	14376	11
145	2009	14728	11
146	2008	14767	11
147	2007	14994	11
148	2006	15387	11
149	2005	16448	11
150	2004	16501	11
151	2003	17073	11
152	2002	18569	11
153	2001	18192	11
154	2000	19377	11
155	2013	8234	12
156	2012	7705	12
157	2011	7952	12
158	2010	8672	12
159	2009	8339	12
160	2008	8310	12
161	2007	8732	12
162	2006	7948	12
163	2005	8440	12
164	2004	8321	12
165	2003	9053	12
166	2002	8891	12
167	2001	8615	12
168	2000	8863	12
169	2013	6607	13
170	2012	6400	13
171	2011	6748	13
172	2010	6795	13
173	2009	6717	13
174	2008	6697	13
175	2007	6670	13
176	2006	6831	13
177	2005	7018	13
178	2004	6839	13
179	2003	6734	13
180	2002	6678	13
181	2001	6404	13
182	2000	6225	13
183	2013	5923	14
184	2012	5549	14
185	2011	5732	14
186	2010	5013	14
187	2009	5190	14
188	2008	4668	14
189	2007	4389	14
190	2006	4267	14
191	2005	4306	14
192	2004	4117	14
193	2003	4089	14
194	2002	3871	14
195	2001	3811	14
196	2000	3475	14
197	2013	5889	15
198	2012	5911	15
199	2011	5666	15
200	2010	5508	15
201	2009	5235	15
202	2008	5148	15
203	2007	4799	15
204	2006	4688	15
205	2005	4788	15
206	2004	4515	15
207	2003	4595	15
208	2002	4218	15
209	2001	4015	15
210	2000	3835	15
211	2013	5889	16
212	2012	5647	16
213	2011	5451	16
214	2010	5393	16
215	2009	5340	16
216	2008	5037	16
217	2007	5093	16
218	2006	5092	16
219	2005	4839	16
220	2004	4818	16
221	2003	4751	16
222	2002	4462	16
223	2001	4203	16
224	2000	4169	16
225	2013	5476	17
226	2012	5578	17
227	2011	5557	17
228	2010	5599	17
229	2009	5508	17
230	2008	5509	17
231	2007	5346	17
232	2006	5362	17
233	2005	5328	17
234	2004	5245	17
235	2003	5185	17
236	2002	5117	17
237	2001	4986	17
238	2000	4980	17
239	2013	5475	18
240	2012	5663	18
241	2011	5258	18
242	2010	5094	18
243	2009	4944	18
244	2008	4840	18
245	2007	4632	18
246	2006	4487	18
247	2005	4264	18
248	2004	4205	18
249	2003	3933	18
250	2002	3919	18
251	2001	3654	18
252	2000	3503	18
253	2013	4977	19
254	2012	4974	19
255	2011	5043	19
256	2010	4860	19
257	2009	5121	19
258	2008	5183	19
259	2007	4959	19
260	2006	4944	19
261	2005	4650	19
262	2004	4719	19
263	2003	4607	19
264	2002	4463	19
265	2001	4317	19
266	2000	4196	19
267	2013	3784	20
268	2012	3840	20
269	2011	3927	20
270	2010	3959	20
271	2009	4107	20
272	2008	4031	20
273	2007	4037	20
274	2006	4131	20
275	2005	4270	20
276	2004	4245	20
277	2003	4324	20
278	2002	4323	20
279	2001	4501	20
280	2000	4604	20
\.


--
-- Name: disease_mortalityyears_id_seq; Type: SEQUENCE SET; Schema: public; Owner: agmartinez
--

SELECT pg_catalog.setval('disease_mortalityyears_id_seq', 280, true);


--
-- PostgreSQL database dump complete
--

