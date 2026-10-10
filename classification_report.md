```text
Auto-detecting Kaggle dataset paths...
Evaluating on: cuda
Model loaded successfully!
Mapping HAM10000 images...
Mapping Fitzpatrick17k images...
Total valid test images found across datasets: 25519
Running inference... this will take a few minutes.

==================================================
🔥 OVERALL ACCURACY: 71.99%
==================================================
```

| Class | Precision | Recall | F1-Score | Support |
|:---|---:|---:|---:|---:|
| fitz_acanthosis_nigricans | 0.83 | 0.80 | 0.81 | 89 |
| fitz_acne | 0.67 | 0.77 | 0.72 | 180 |
| fitz_acne_vulgaris | 0.82 | 0.83 | 0.82 | 333 |
| fitz_acquired_autoimmune_bullous_diseaseherpes_gestationis | 0.55 | 0.82 | 0.66 | 67 |
| fitz_acrodermatitis_enteropathica | 0.76 | 0.90 | 0.82 | 91 |
| fitz_actinic_keratosis | 0.59 | 0.69 | 0.64 | 169 |
| fitz_allergic_contact_dermatitis | 0.68 | 0.39 | 0.50 | 425 |
| fitz_aplasia_cutis | 0.61 | 0.81 | 0.70 | 27 |
| fitz_basal_cell_carcinoma | 0.81 | 0.64 | 0.72 | 452 |
| fitz_basal_cell_carcinoma_morpheiform | 0.66 | 0.86 | 0.75 | 58 |
| fitz_becker_nevus | 0.73 | 0.86 | 0.79 | 56 |
| fitz_behcets_disease | 0.57 | 0.75 | 0.65 | 36 |
| fitz_calcinosis_cutis | 0.74 | 0.81 | 0.77 | 78 |
| fitz_cheilitis | 0.75 | 0.83 | 0.79 | 83 |
| fitz_congenital_nevus | 0.83 | 0.88 | 0.85 | 66 |
| fitz_dariers_disease | 0.73 | 0.82 | 0.77 | 151 |
| fitz_dermatofibroma | 0.56 | 0.86 | 0.68 | 78 |
| fitz_dermatomyositis | 0.69 | 0.70 | 0.70 | 151 |
| fitz_disseminated_actinic_porokeratosis | 0.69 | 0.97 | 0.80 | 59 |
| fitz_drug_eruption | 0.62 | 0.62 | 0.62 | 194 |
| fitz_drug_induced_pigmentary_changes | 0.80 | 0.76 | 0.78 | 70 |
| fitz_dyshidrotic_eczema | 0.66 | 0.81 | 0.73 | 80 |
| fitz_eczema | 0.60 | 0.62 | 0.61 | 200 |
| fitz_ehlers_danlos_syndrome | 0.88 | 0.90 | 0.89 | 126 |
| fitz_epidermal_nevus | 0.77 | 0.81 | 0.79 | 88 |
| fitz_epidermolysis_bullosa | 0.75 | 0.75 | 0.75 | 67 |
| fitz_erythema_annulare_centrifigum | 0.77 | 0.93 | 0.85 | 88 |
| fitz_erythema_elevatum_diutinum | 0.64 | 0.87 | 0.74 | 55 |
| fitz_erythema_multiforme | 0.78 | 0.75 | 0.76 | 227 |
| fitz_erythema_nodosum | 0.71 | 0.90 | 0.79 | 81 |
| fitz_factitial_dermatitis | 0.66 | 0.80 | 0.72 | 65 |
| fitz_fixed_eruptions | 0.80 | 0.80 | 0.80 | 124 |
| fitz_folliculitis | 0.71 | 0.81 | 0.76 | 299 |
| fitz_fordyce_spots | 0.77 | 0.88 | 0.82 | 52 |
| fitz_granuloma_annulare | 0.82 | 0.78 | 0.80 | 211 |
| fitz_granuloma_pyogenic | 0.74 | 0.93 | 0.82 | 67 |
| fitz_hailey_hailey_disease | 0.86 | 0.97 | 0.91 | 172 |
| fitz_halo_nevus | 0.84 | 0.87 | 0.86 | 78 |
| fitz_hidradenitis | 0.75 | 0.92 | 0.83 | 90 |
| fitz_ichthyosis_vulgaris | 0.74 | 0.92 | 0.82 | 62 |
| fitz_incontinentia_pigmenti | 0.73 | 0.83 | 0.77 | 99 |
| fitz_juvenile_xanthogranuloma | 0.87 | 0.83 | 0.85 | 130 |
| fitz_kaposi_sarcoma | 0.81 | 0.86 | 0.84 | 145 |
| fitz_keloid | 0.91 | 0.92 | 0.92 | 155 |
| fitz_keratosis_pilaris | 0.61 | 0.86 | 0.71 | 78 |
| fitz_langerhans_cell_histiocytosis | 0.74 | 0.83 | 0.78 | 52 |
| fitz_lentigo_maligna | 0.51 | 0.79 | 0.62 | 78 |
| fitz_lichen_amyloidosis | 0.84 | 0.95 | 0.89 | 75 |
| fitz_lichen_planus | 0.84 | 0.56 | 0.67 | 440 |
| fitz_lichen_simplex | 0.70 | 0.80 | 0.75 | 97 |
| fitz_livedo_reticularis | 0.78 | 0.90 | 0.84 | 60 |
| fitz_lupus_erythematosus | 0.76 | 0.57 | 0.65 | 382 |
| fitz_lupus_subacute | 0.60 | 0.76 | 0.67 | 99 |
| fitz_lyme_disease | 0.66 | 0.81 | 0.73 | 129 |
| fitz_lymphangioma | 0.69 | 0.78 | 0.73 | 81 |
| fitz_malignant_melanoma | 0.61 | 0.76 | 0.68 | 102 |
| fitz_melanoma | 0.76 | 0.75 | 0.75 | 248 |
| fitz_milia | 0.63 | 0.83 | 0.72 | 110 |
| fitz_mucinosis | 0.71 | 0.86 | 0.78 | 84 |
| fitz_mucous_cyst | 0.56 | 0.80 | 0.66 | 45 |
| fitz_mycosis_fungoides | 0.83 | 0.80 | 0.81 | 181 |
| fitz_myiasis | 0.85 | 0.83 | 0.84 | 42 |
| fitz_naevus_comedonicus | 0.82 | 0.86 | 0.84 | 73 |
| fitz_necrobiosis_lipoidica | 0.77 | 0.91 | 0.83 | 122 |
| fitz_nematode_infection | 0.81 | 0.94 | 0.87 | 260 |
| fitz_neurodermatitis | 0.49 | 0.75 | 0.59 | 69 |
| fitz_neurofibromatosis | 0.85 | 0.94 | 0.89 | 188 |
| fitz_neurotic_excoriations | 0.70 | 0.81 | 0.75 | 73 |
| fitz_neutrophilic_dermatoses | 0.81 | 0.72 | 0.76 | 344 |
| fitz_nevocytic_nevus | 0.23 | 0.88 | 0.37 | 82 |
| fitz_nevus_sebaceous_of_jadassohn | 0.67 | 0.87 | 0.76 | 54 |
| fitz_papilomatosis_confluentes_and_reticulate | 0.88 | 0.96 | 0.92 | 149 |
| fitz_paronychia | 0.64 | 0.90 | 0.75 | 58 |
| fitz_pediculosis_lids | 0.76 | 0.96 | 0.85 | 69 |
| fitz_perioral_dermatitis | 0.64 | 0.82 | 0.72 | 61 |
| fitz_photodermatoses | 0.72 | 0.41 | 0.53 | 344 |
| fitz_pilar_cyst | 0.71 | 0.84 | 0.77 | 75 |
| fitz_pilomatricoma | 0.84 | 0.78 | 0.81 | 49 |
| fitz_pityriasis_lichenoides_chronica | 0.68 | 0.88 | 0.77 | 73 |
| fitz_pityriasis_rosea | 0.72 | 0.84 | 0.78 | 193 |
| fitz_pityriasis_rubra_pilaris | 0.88 | 0.88 | 0.88 | 273 |
| fitz_porokeratosis_actinic | 0.81 | 0.90 | 0.85 | 180 |
| fitz_porokeratosis_of_mibelli | 0.77 | 0.90 | 0.83 | 78 |
| fitz_porphyria | 0.75 | 0.84 | 0.79 | 124 |
| fitz_port_wine_stain | 0.52 | 0.80 | 0.63 | 59 |
| fitz_prurigo_nodularis | 0.75 | 0.92 | 0.83 | 170 |
| fitz_psoriasis | 0.80 | 0.52 | 0.63 | 615 |
| fitz_pustular_psoriasis | 0.51 | 0.83 | 0.63 | 53 |
| fitz_pyogenic_granuloma | 0.72 | 0.79 | 0.76 | 102 |
| fitz_rhinophyma | 0.81 | 0.96 | 0.87 | 91 |
| fitz_rosacea | 0.68 | 0.69 | 0.68 | 102 |
| fitz_sarcoidosis | 0.69 | 0.53 | 0.60 | 329 |
| fitz_scabies | 0.86 | 0.81 | 0.83 | 306 |
| fitz_scleroderma | 0.72 | 0.61 | 0.66 | 299 |
| fitz_scleromyxedema | 0.83 | 0.88 | 0.86 | 108 |
| fitz_seborrheic_dermatitis | 0.72 | 0.80 | 0.76 | 116 |
| fitz_seborrheic_keratosis | 0.76 | 0.84 | 0.79 | 67 |
| fitz_solid_cystic_basal_cell_carcinoma | 0.53 | 0.84 | 0.65 | 61 |
| fitz_squamous_cell_carcinoma | 0.83 | 0.66 | 0.73 | 490 |
| fitz_stasis_edema | 0.57 | 0.82 | 0.67 | 68 |
| fitz_stevens_johnson_syndrome | 0.71 | 0.88 | 0.79 | 101 |
| fitz_striae | 0.79 | 0.85 | 0.82 | 66 |
| fitz_sun_damaged_skin | 0.59 | 0.71 | 0.65 | 66 |
| fitz_superficial_spreading_melanoma_ssm | 0.57 | 0.88 | 0.69 | 114 |
| fitz_syringoma | 0.87 | 0.89 | 0.88 | 121 |
| fitz_telangiectases | 0.73 | 0.76 | 0.74 | 123 |
| fitz_tick_bite | 0.79 | 0.81 | 0.80 | 68 |
| fitz_tuberous_sclerosis | 0.84 | 0.85 | 0.85 | 132 |
| fitz_tungiasis | 0.83 | 0.97 | 0.90 | 76 |
| fitz_urticaria | 0.76 | 0.74 | 0.75 | 151 |
| fitz_urticaria_pigmentosa | 0.69 | 0.69 | 0.69 | 111 |
| fitz_vitiligo | 0.81 | 0.86 | 0.83 | 159 |
| fitz_xanthomas | 0.80 | 0.75 | 0.77 | 52 |
| fitz_xeroderma_pigmentosum | 0.90 | 0.86 | 0.88 | 80 |
| ham_akiec | 0.61 | 0.80 | 0.69 | 327 |
| ham_bcc | 0.68 | 0.91 | 0.78 | 514 |
| ham_bkl | 0.69 | 0.57 | 0.63 | 1099 |
| ham_df | 0.66 | 0.97 | 0.79 | 115 |
| ham_mel | 0.32 | 0.83 | 0.47 | 1113 |
| ham_nv | 0.98 | 0.61 | 0.75 | 6705 |
| ham_vasc | 0.49 | 0.96 | 0.65 | 142 |
| **accuracy** | | | **0.72** | **25519** |
| **macro avg** | **0.72** | **0.81** | **0.75** | **25519** |
| **weighted avg** | **0.78** | **0.72** | **0.73** | **25519** |