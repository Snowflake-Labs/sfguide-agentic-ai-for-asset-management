# Copyright 2026 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Simulated Asset Management (SAM) Demo Configuration
All configuration constants for the SAM AI demo using CAPS naming convention.
"""

import os
import sys

# #############################################################################
#
#                       USER-EDITABLE SETTINGS
#
#  The settings below are the most commonly changed by users. Modify these
#  first when customizing the demo for your environment.
#
# #############################################################################

# =============================================================================
# CONNECTION & CORE BUILD SETTINGS
# =============================================================================

# Snowflake connection name (from ~/.snowflake/connections.toml)
DEFAULT_CONNECTION_NAME = 'sfseeurope-mstellwall-aws-us-west3'

# Seed for reproducible random generation (change to get different deterministic output)
RNG_SEED = 42

# Historical data range (years of position/transaction history to generate)
YEARS_OF_HISTORY = 5

# Test mode multiplier - scales down data volumes for faster dev builds (e.g. 0.1 = 10%)
TEST_MODE_MULTIPLIER = 0.1

# =============================================================================
# AI MODEL CONFIGURATION
# =============================================================================

# Model used for speaker identification in transcript processing (AI_COMPLETE)
# Options: 'claude-haiku-4-5', 'claude-sonnet-4', 'llama3.1-8b', etc.
AI_SPEAKER_IDENTIFICATION_MODEL = 'claude-haiku-4-5'

# Model used for agent orchestration (Snowflake Intelligence agents)
AGENT_ORCHESTRATION_MODEL = 'claude-sonnet-4-5'

# Model used for text embeddings (Cortex Search, token counting)
AI_EMBEDDING_MODEL = 'snowflake-arctic-embed-m-v1.5'

# =============================================================================
# DATABASE & WAREHOUSE CONFIGURATION
# =============================================================================

DATABASE = {
    'name': 'SAM_DEMO',
    'schemas': {
        'raw': 'RAW',
        'curated': 'CURATED',
        'ai': 'AI',
        'market_data': 'MARKET_DATA'  # External provider data (financial statements, estimates, filings)
    }
}

WAREHOUSES = {
    'execution': {
        'name': 'SAM_DEMO_WH',
        'size': 'LARGE',
        'comment': 'Warehouse for SAM demo data generation and execution'
    },
    'cortex_search': {
        'name': 'SAM_DEMO_WH',
        'size': 'LARGE',
        'target_lag': '1 hour',
        'comment': 'Warehouse for SAM demo Cortex Search services'
    }
}

# =============================================================================
# REAL DATA SOURCES (external public data shares)
# =============================================================================
#
# Point these to your public data share. The tables dict is defined later in
# REAL_DATA_SOURCES_TABLES and attached to this dict after the file loads.
#
REAL_DATA_SOURCES = {
    # -------------------------------------------------------------------------
    # Change these two values to match your Snowflake Marketplace data share
    # -------------------------------------------------------------------------
    'database': 'SNOWFLAKE_PUBLIC_DATA_FREE',  # e.g. 'SNOWFLAKE_PUBLIC_DATA_FREE'
    'schema': 'PUBLIC_DATA_FREE',              # e.g. 'PUBLIC_DATA_FREE'

    # Key into REAL_DATA_SOURCES['tables'] to probe for share access (must exist in share)
    # IMPORTANT: This data source is REQUIRED. The build will fail if not accessible.
    'access_probe_table_key': 'sec_metrics'
}

# =============================================================================
# DEMO COMPANIES - Single Source of Truth for Company Data
# =============================================================================
#
# This is the authoritative list of companies used in the demo. All data generation
# (DIM_ISSUER, DIM_SECURITY, transcripts, market data, documents) flows from this list.
#
# Structure:
#   - provider_company_id: COMPANY_ID from SNOWFLAKE_PUBLIC_DATA_FREE.COMPANY_INDEX
#   - cik: SEC Central Index Key for SEC filings and transcripts
#   - tier: 'core' (demo scenarios), 'major' (well-known), 'additional' (variety)
#
# Total: ~76 companies (8 core + 36 major + 32 additional)
#

DEMO_COMPANIES = {
    # =========================================================================
    # CORE DEMO COMPANIES (featured in demo scenarios)
    # =========================================================================
    'AAPL': {
        'company_name': 'APPLE INC.',
        'provider_company_id': 'a1823f6c7cd49c0be0bb8c43bcf49060',
        'cik': '0000320193',
        'sector': 'Information Technology',
        'tier': 'core',
        'demo_order': 1,           # Priority order in demo portfolios
        'position_size': 'large'   # Large position for prominent display
    },
    'CMC': {
        'company_name': 'COMMERCIAL METALS CO',
        'provider_company_id': '50b5c4a14b7d9817e50d66022153a149',
        'cik': '0000022444',
        'sector': 'Materials',
        'tier': 'core',
        'demo_order': 2,
        'position_size': 'large'
    },
    'RBBN': {
        'company_name': 'RIBBON COMMUNICATIONS INC.',
        'provider_company_id': '2ce2d9e86f2421124050cb4e862f3be7',
        'cik': '0001708055',
        'sector': 'Information Technology',
        'tier': 'core',
        'demo_order': 3,
        'position_size': 'large'
    },
    'MSFT': {
        'company_name': 'MICROSOFT CORP',
        'provider_company_id': 'ac0b3684602d98a5f168564f3f3af882',
        'cik': '0000789019',
        'sector': 'Information Technology',
        'tier': 'core',
        'demo_order': 4            # Additional demo holding (no large position)
    },
    'NVDA': {
        'company_name': 'NVIDIA CORP',
        'provider_company_id': '59cf1797ff7546139b04473f612cbe0c',
        'cik': '0001045810',
        'sector': 'Information Technology',
        'tier': 'core',
        'demo_order': 5
    },
    'GOOGL': {
        'company_name': 'ALPHABET INC.',
        'provider_company_id': 'bec137cd76d8c4d1440569461d7375bd',
        'cik': '0001652044',
        'sector': 'Communication Services',
        'tier': 'core',
        'demo_order': 6
    },
    'TSM': {
        'company_name': 'TAIWAN SEMICONDUCTOR MANUFACTURING CO LTD',
        'provider_company_id': '71ae635a2d258f8bdb7c7c8bf06b3811',
        'cik': '0001046179',
        'sector': 'Information Technology',
        'tier': 'core'
    },
    'SNOW': {
        'company_name': 'SNOWFLAKE INC.',
        'provider_company_id': 'be66d09336f7d9b9b53c3e129f241a11',
        'cik': '0001640147',
        'sector': 'Information Technology',
        'tier': 'core'
    },
    
    # =========================================================================
    # MAJOR US STOCKS (well-known companies for portfolio diversity)
    # =========================================================================
    'ABT': {
        'company_name': 'ABBOTT LABORATORIES',
        'provider_company_id': '2dcb8bc8661e611361f7c0254cb02ee7',
        'cik': '0000001800',
        'sector': 'Healthcare',
        'tier': 'major'
    },
    'ADBE': {
        'company_name': 'ADOBE INC.',
        'provider_company_id': 'fe47832b8f820a17fd8d6308942390f9',
        'cik': '0000796343',
        'sector': 'Information Technology',
        'tier': 'major'
    },
    'AMZN': {
        'company_name': 'AMAZON COM INC',
        'provider_company_id': '602fec4b30df7a598a17a09fa789cc48',
        'cik': '0001018724',
        'sector': 'Consumer Discretionary',
        'tier': 'major'
    },
    'BA': {
        'company_name': 'BOEING CO',
        'provider_company_id': '68c9c4dd104ff90807898f9a7aa4e0d6',
        'cik': '0000012927',
        'sector': 'Industrials',
        'tier': 'major'
    },
    'BAC': {
        'company_name': 'BANK OF AMERICA CORP /DE/',
        'provider_company_id': '9a845a21be69d75e3926bba3a30347fc',
        'cik': '0000070858',
        'sector': 'Financials',
        'tier': 'major'
    },
    'CAT': {
        'company_name': 'CATERPILLAR INC',
        'provider_company_id': 'd7fbbcb4f157933eccffc75c755fab39',
        'cik': '0000018230',
        'sector': 'Industrials',
        'tier': 'major'
    },
    'COST': {
        'company_name': 'COSTCO WHOLESALE CORP /NEW',
        'provider_company_id': 'ac487d6576dde56b4942173b146faf84',
        'cik': '0000909832',
        'sector': 'Consumer Staples',
        'tier': 'major'
    },
    'CRM': {
        'company_name': 'SALESFORCE, INC.',
        'provider_company_id': 'bd894082fd352970647a92c1df99881c',
        'cik': '0001108524',
        'sector': 'Information Technology',
        'tier': 'major'
    },
    'CVX': {
        'company_name': 'CHEVRON CORP',
        'provider_company_id': '08cbcbca1fc39748660d8d36bb626500',
        'cik': '0000093410',
        'sector': 'Energy',
        'tier': 'major'
    },
    'DIS': {
        'company_name': 'WALT DISNEY CO',
        'provider_company_id': 'c78f2872321b60ff3fa49ada08125976',
        'cik': '0001744489',
        'sector': 'Communication Services',
        'tier': 'major'
    },
    'GE': {
        'company_name': 'GENERAL ELECTRIC CO',
        'provider_company_id': '5477805a8d1d1a891997fdb23940dec4',
        'cik': '0000040545',
        'sector': 'Industrials',
        'tier': 'major'
    },
    'GS': {
        'company_name': 'GOLDMAN SACHS GROUP INC',
        'provider_company_id': '16b8b3d1cf68327f043f2828a308bb2b',
        'cik': '0000886982',
        'sector': 'Financials',
        'tier': 'major'
    },
    'HD': {
        'company_name': 'HOME DEPOT, INC.',
        'provider_company_id': '20d74b93038d934d279f5018dfeab566',
        'cik': '0000354950',
        'sector': 'Consumer Discretionary',
        'tier': 'major'
    },
    'HON': {
        'company_name': 'HONEYWELL INTERNATIONAL INC',
        'provider_company_id': '065bb5fb539b0088c252b64eb3238b9a',
        'cik': '0000773840',
        'sector': 'Industrials',
        'tier': 'major'
    },
    'IBM': {
        'company_name': 'INTERNATIONAL BUSINESS MACHINES CORP',
        'provider_company_id': '08391471747f5b9c97c4ec1b8b1cc389',
        'cik': '0000051143',
        'sector': 'Information Technology',
        'tier': 'major'
    },
    'INTC': {
        'company_name': 'INTEL CORP',
        'provider_company_id': '33c4c5960af4e6eb8dd18d4ec982c0c2',
        'cik': '0000050863',
        'sector': 'Information Technology',
        'tier': 'major'
    },
    'JNJ': {
        'company_name': 'JOHNSON & JOHNSON',
        'provider_company_id': 'bd9c926b9a88a238a0ff54be08a9ec7d',
        'cik': '0000200406',
        'sector': 'Healthcare',
        'tier': 'major'
    },
    'JPM': {
        'company_name': 'JPMORGAN CHASE & CO',
        'provider_company_id': '23525aaf57004d0109af27c0476ed582',
        'cik': '0000019617',
        'sector': 'Financials',
        'tier': 'major'
    },
    'KO': {
        'company_name': 'COCA COLA CO',
        'provider_company_id': 'cf56194869c92a1a3b1471e74eb596e6',
        'cik': '0000021344',
        'sector': 'Consumer Staples',
        'tier': 'major'
    },
    'MA': {
        'company_name': 'MASTERCARD INC',
        'provider_company_id': '4b0db043c6fc123bbcff2427f592c1f7',
        'cik': '0001141391',
        'sector': 'Financials',
        'tier': 'major'
    },
    'MCD': {
        'company_name': 'MCDONALDS CORP',
        'provider_company_id': 'd06d310eb441913b0e7491ea0ab7b7a7',
        'cik': '0000063908',
        'sector': 'Consumer Discretionary',
        'tier': 'major'
    },
    'META': {
        'company_name': 'META PLATFORMS, INC.',
        'provider_company_id': 'ab379e8e0b5beed5fb6053e34e5c20f5',
        'cik': '0001326801',
        'sector': 'Communication Services',
        'tier': 'major'
    },
    'MMM': {
        'company_name': '3M CO',
        'provider_company_id': 'd4b5a9265d9060a018829797de5e5b55',
        'cik': '0000066740',
        'sector': 'Industrials',
        'tier': 'major'
    },
    'MRK': {
        'company_name': 'MERCK & CO., INC.',
        'provider_company_id': '6fdd33c17560666c2938b7fb60c6e1d1',
        'cik': '0000310158',
        'sector': 'Healthcare',
        'tier': 'major'
    },
    'NFLX': {
        'company_name': 'NETFLIX INC',
        'provider_company_id': 'db2f01cb35f46c6be97dbf391a143572',
        'cik': '0001065280',
        'sector': 'Communication Services',
        'tier': 'major'
    },
    'NKE': {
        'company_name': 'NIKE, INC.',
        'provider_company_id': '3894632f0ef9f020ea609701d68ee1a0',
        'cik': '0000320187',
        'sector': 'Consumer Discretionary',
        'tier': 'major'
    },
    'PEP': {
        'company_name': 'PEPSICO INC',
        'provider_company_id': '1146156f378520a0c016c884431e8361',
        'cik': '0000077476',
        'sector': 'Consumer Staples',
        'tier': 'major'
    },
    'PFE': {
        'company_name': 'PFIZER INC',
        'provider_company_id': '2504b4544c6fa9591220676dbd4800f3',
        'cik': '0000078003',
        'sector': 'Healthcare',
        'tier': 'major'
    },
    'PG': {
        'company_name': 'PROCTER & GAMBLE CO',
        'provider_company_id': 'efff2e4e63cd1c6744b1b60544f1b08f',
        'cik': '0000080424',
        'sector': 'Consumer Staples',
        'tier': 'major'
    },
    'RTX': {
        'company_name': 'RTX CORP',
        'provider_company_id': 'f2a507315f1e348ada4b39d295f787c6',
        'cik': '0000101829',
        'sector': 'Industrials',
        'tier': 'major'
    },
    'TMO': {
        'company_name': 'THERMO FISHER SCIENTIFIC INC.',
        'provider_company_id': '003eb2b65f0d8ce5298bc1c4298a99f3',
        'cik': '0000097745',
        'sector': 'Healthcare',
        'tier': 'major'
    },
    'TSLA': {
        'company_name': 'TESLA, INC.',
        'provider_company_id': 'b1e8d2d49d41f1e194dce9e2492553a2',
        'cik': '0001318605',
        'sector': 'Consumer Discretionary',
        'tier': 'major'
    },
    'UPS': {
        'company_name': 'UNITED PARCEL SERVICE INC',
        'provider_company_id': 'd2d38a33a63c33a38a567435516efb40',
        'cik': '0001090727',
        'sector': 'Industrials',
        'tier': 'major'
    },
    'V': {
        'company_name': 'VISA INC.',
        'provider_company_id': '2af6dd0f1722e0932d070172539035cb',
        'cik': '0001403161',
        'sector': 'Financials',
        'tier': 'major'
    },
    'VZ': {
        'company_name': 'VERIZON COMMUNICATIONS INC',
        'provider_company_id': '5fdfa3a85e7855ee604954dc4555ca69',
        'cik': '0000732712',
        'sector': 'Communication Services',
        'tier': 'major'
    },
    'WMT': {
        'company_name': 'WALMART INC.',
        'provider_company_id': '960989974008dcda4b78eed24a8dfd79',
        'cik': '0000104169',
        'sector': 'Consumer Staples',
        'tier': 'major'
    },
    
    # =========================================================================
    # ADDITIONAL COMPANIES (for variety and sector coverage)
    # =========================================================================
    'ABBV': {
        'company_name': 'ABBVIE INC.',
        'provider_company_id': 'bed33a415019b73b323407510571b44b',
        'cik': '0001551152',
        'sector': 'Healthcare',
        'tier': 'additional'
    },
    'ACN': {
        'company_name': 'ACCENTURE PLC',
        'provider_company_id': '6dd20bd08f395569ae637fb55d268e9a',
        'cik': '0001467373',
        'sector': 'Information Technology',
        'tier': 'additional'
    },
    'AMD': {
        'company_name': 'ADVANCED MICRO DEVICES INC',
        'provider_company_id': '12c617b47081d343dc595256aa5bbb1d',
        'cik': '0000002488',
        'sector': 'Information Technology',
        'tier': 'additional'
    },
    'AMGN': {
        'company_name': 'AMGEN INC',
        'provider_company_id': 'b8eb503baf67da0d656418f26d86a247',
        'cik': '0000318154',
        'sector': 'Healthcare',
        'tier': 'additional'
    },
    'AVGO': {
        'company_name': 'BROADCOM INC.',
        'provider_company_id': '8f448325fadfc6891e19cbaddff9ca2f',
        'cik': '0001730168',
        'sector': 'Information Technology',
        'tier': 'additional'
    },
    'AXP': {
        'company_name': 'AMERICAN EXPRESS CO',
        'provider_company_id': 'c215acdc7197fa4724d1f021fdd70b2e',
        'cik': '0000004962',
        'sector': 'Financials',
        'tier': 'additional'
    },
    'BLK': {
        'company_name': 'BLACKROCK, INC.',
        'provider_company_id': 'aaa6fa94007b48fd4da6d273546b7cc5',
        'cik': '0002012383',
        'sector': 'Financials',
        'tier': 'additional'
    },
    'BMY': {
        'company_name': 'BRISTOL MYERS SQUIBB CO',
        'provider_company_id': '1f067fb3fa6f230c4ed58948d667225a',
        'cik': '0000014272',
        'sector': 'Healthcare',
        'tier': 'additional'
    },
    'C': {
        'company_name': 'CITIGROUP INC',
        'provider_company_id': '28603c252e64cb45a30b5c40efddba18',
        'cik': '0000831001',
        'sector': 'Financials',
        'tier': 'additional'
    },
    'CMCSA': {
        'company_name': 'COMCAST CORP',
        'provider_company_id': 'cfa580e9411379ead0ee52747ab10f0f',
        'cik': '0001166691',
        'sector': 'Communication Services',
        'tier': 'additional'
    },
    'COP': {
        'company_name': 'CONOCOPHILLIPS',
        'provider_company_id': 'e4678ce6da016a603d7646feb4473776',
        'cik': '0001163165',
        'sector': 'Energy',
        'tier': 'additional'
    },
    'CSCO': {
        'company_name': 'CISCO SYSTEMS INC',
        'provider_company_id': 'f41bca735f7d5bb1632f38397a005040',
        'cik': '0000858877',
        'sector': 'Information Technology',
        'tier': 'additional'
    },
    'DE': {
        'company_name': 'DEERE & CO',
        'provider_company_id': '13b9e4c3888fb26f28f7d66ddc2d3d71',
        'cik': '0000315189',
        'sector': 'Industrials',
        'tier': 'additional'
    },
    'GILD': {
        'company_name': 'GILEAD SCIENCES, INC.',
        'provider_company_id': 'ed34f0e78d4ee741356045ac3f8939df',
        'cik': '0000882095',
        'sector': 'Healthcare',
        'tier': 'additional'
    },
    'INTU': {
        'company_name': 'INTUIT INC.',
        'provider_company_id': '0cee4af2a74f2156d5c041655d171006',
        'cik': '0000896878',
        'sector': 'Information Technology',
        'tier': 'additional'
    },
    'LLY': {
        'company_name': 'ELI LILLY & CO',
        'provider_company_id': 'a1f97674b098caf30e9b61b98e06ea49',
        'cik': '0000059478',
        'sector': 'Healthcare',
        'tier': 'additional'
    },
    'LMT': {
        'company_name': 'LOCKHEED MARTIN CORP',
        'provider_company_id': 'a533e245225fe0c914004e378f369224',
        'cik': '0000936468',
        'sector': 'Industrials',
        'tier': 'additional'
    },
    'LOW': {
        'company_name': 'LOWES COMPANIES INC',
        'provider_company_id': '9d39036436c25d64d45efc7a12a41ff9',
        'cik': '0000060667',
        'sector': 'Consumer Discretionary',
        'tier': 'additional'
    },
    'MO': {
        'company_name': 'ALTRIA GROUP, INC.',
        'provider_company_id': '07a650ec3d64b0309afa6be95872f5be',
        'cik': '0000764180',
        'sector': 'Consumer Staples',
        'tier': 'additional'
    },
    'NOW': {
        'company_name': 'SERVICENOW, INC.',
        'provider_company_id': '4e2ddb5d8358fd82e6b71be0dcf6f02e',
        'cik': '0001373715',
        'sector': 'Information Technology',
        'tier': 'additional'
    },
    'ORCL': {
        'company_name': 'ORACLE CORP',
        'provider_company_id': '55e0983aa1cd07da5580c6c6069e6b67',
        'cik': '0001341439',
        'sector': 'Information Technology',
        'tier': 'additional'
    },
    'PM': {
        'company_name': 'PHILIP MORRIS INTERNATIONAL INC.',
        'provider_company_id': 'f0b74ca7f8422c56abc878bbbfce8675',
        'cik': '0001413329',
        'sector': 'Consumer Staples',
        'tier': 'additional'
    },
    'QCOM': {
        'company_name': 'QUALCOMM INC/DE',
        'provider_company_id': 'a66fa1ce7129d8898f49d981f90e2f29',
        'cik': '0000804328',
        'sector': 'Information Technology',
        'tier': 'additional'
    },
    'SBUX': {
        'company_name': 'STARBUCKS CORP',
        'provider_company_id': '0977f0d1649a6eb6d1c1a95b6a967bde',
        'cik': '0000829224',
        'sector': 'Consumer Discretionary',
        'tier': 'additional'
    },
    'SCHW': {
        'company_name': 'SCHWAB CHARLES CORP',
        'provider_company_id': '1d82f5e406753c1e980247597d8c0946',
        'cik': '0000316709',
        'sector': 'Financials',
        'tier': 'additional'
    },
    'T': {
        'company_name': 'AT&T INC.',
        'provider_company_id': 'ec93708b0ebab2ca2cb98b43bfb695f4',
        'cik': '0000732717',
        'sector': 'Communication Services',
        'tier': 'additional'
    },
    'TGT': {
        'company_name': 'TARGET CORP',
        'provider_company_id': 'e308587f750017801f5df278c74eae5a',
        'cik': '0000027419',
        'sector': 'Consumer Discretionary',
        'tier': 'additional'
    },
    'TMUS': {
        'company_name': 'T-MOBILE US, INC.',
        'provider_company_id': '8db7e0f28fc9707b06afcba0c45b24f3',
        'cik': '0001283699',
        'sector': 'Communication Services',
        'tier': 'additional'
    },
    'TXN': {
        'company_name': 'TEXAS INSTRUMENTS INC',
        'provider_company_id': '94b4acfb3b974d8a7a8d28b3c1b6458b',
        'cik': '0000097476',
        'sector': 'Information Technology',
        'tier': 'additional'
    },
    'UNH': {
        'company_name': 'UNITEDHEALTH GROUP INC',
        'provider_company_id': 'd7327699823b42ebf25763acb8fe2205',
        'cik': '0000731766',
        'sector': 'Healthcare',
        'tier': 'additional'
    },
    'UNP': {
        'company_name': 'UNION PACIFIC CORP',
        'provider_company_id': '8a47cbfea6e5eef94e50408174059610',
        'cik': '0000100885',
        'sector': 'Industrials',
        'tier': 'additional'
    },
    'WFC': {
        'company_name': 'WELLS FARGO & COMPANY/MN',
        'provider_company_id': '5bea05cafd8529c8d75f5209f36ed393',
        'cik': '0000072971',
        'sector': 'Financials',
        'tier': 'additional'
    },
    'XOM': {
        'company_name': 'EXXON MOBIL CORP',
        'provider_company_id': '1a8f6bfe3e62cee3474fa4b5c4e30c95',
        'cik': '0000034088',
        'sector': 'Energy',
        'tier': 'additional'
    },
    
    # =========================================================================
    # SUPPLY CHAIN COMPANIES (for second-order risk scenarios)
    # =========================================================================
    'F': {
        'company_name': 'FORD MOTOR CO',
        'provider_company_id': 'f92ae9cf8d2cc81603f73a5ed8adcc09',
        'cik': '0000037996',
        'sector': 'Consumer Discretionary',
        'tier': 'supply_chain'
    },
    'GM': {
        'company_name': 'GENERAL MOTORS CO',
        'provider_company_id': 'ac4dbec3bea72f9baee1526c93bf65e9',
        'cik': '0001467858',
        'sector': 'Consumer Discretionary',
        'tier': 'supply_chain'
    },
}

# Helper functions for DEMO_COMPANIES (moved to demo_helpers.py)
# Re-exported at end of file for backward compatibility

# =============================================================================
# DATE RANGE HELPERS (functions moved to db_helpers.py)
# =============================================================================
# Re-exported at end of file for backward compatibility

# =============================================================================
# DEMO CLIENTS (institutional clients for Sales Advisor & Executive scenarios)
# =============================================================================
# These clients are prioritized in DIM_CLIENT generation with their exact names.
# Used by: Sales Advisor client-specific reporting, Executive Copilot client analytics

# =============================================================================
# DEMO CLIENTS (unified config with category field)
# =============================================================================
# All demo clients in one dictionary. Categories:
#   - 'standard': Regular established clients
#   - 'at_risk': Clients with declining flows (for retention scenarios)
#   - 'new': Recently onboarded clients (for onboarding scenarios)

DEMO_CLIENTS = {
    # --- Standard Clients (established relationships) ---
    'meridian': {
        'client_name': 'Meridian Capital Partners',
        'client_type': 'Pension',
        'region': 'North America',
        'aum_range': (400_000_000, 500_000_000),
        'priority': 1,
        'category': 'standard'
    },
    'blackrock_pension': {
        'client_name': 'Blackrock Pension Trust',
        'client_type': 'Pension',
        'region': 'North America',
        'aum_range': (350_000_000, 450_000_000),
        'priority': 2,
        'category': 'standard'
    },
    'yale_endowment': {
        'client_name': 'Yale University Endowment',
        'client_type': 'Endowment',
        'region': 'North America',
        'aum_range': (300_000_000, 400_000_000),
        'priority': 3,
        'category': 'standard'
    },
    'gates_foundation': {
        'client_name': 'Gates Foundation Trust',
        'client_type': 'Foundation',
        'region': 'North America',
        'aum_range': (250_000_000, 350_000_000),
        'priority': 4,
        'category': 'standard'
    },
    'axa_insurance': {
        'client_name': 'AXA Insurance General Account',
        'client_type': 'Insurance',
        'region': 'Europe',
        'aum_range': (200_000_000, 300_000_000),
        'priority': 5,
        'category': 'standard'
    },
    'toyota_pension': {
        'client_name': 'Toyota Motor Pension Fund',
        'client_type': 'Corporate',
        'region': 'Asia Pacific',
        'aum_range': (150_000_000, 250_000_000),
        'priority': 6,
        'category': 'standard'
    },
    'rockefeller_family': {
        'client_name': 'Rockefeller Family Office',
        'client_type': 'Family Office',
        'region': 'North America',
        'aum_range': (100_000_000, 200_000_000),
        'priority': 7,
        'category': 'standard'
    },
    'norway_sovereign': {
        'client_name': 'Norwegian Sovereign Wealth Fund',
        'client_type': 'Pension',
        'region': 'Europe',
        'aum_range': (450_000_000, 500_000_000),
        'priority': 8,
        'category': 'standard'
    },
    # --- At-Risk Clients (declining flows - for retention scenarios) ---
    'pacific_pension': {
        'client_name': 'Pacific Coast Pension Fund',
        'client_type': 'Pension',
        'region': 'North America',
        'aum_range': (180_000_000, 220_000_000),
        'priority': 9,
        'category': 'at_risk',
        'flow_pattern': 'declining',
        'decline_reason': 'Manager consolidation initiative - reviewing all external relationships'
    },
    'alpine_endowment': {
        'client_name': 'Alpine University Endowment',
        'client_type': 'Endowment',
        'region': 'North America',
        'aum_range': (80_000_000, 120_000_000),
        'priority': 10,
        'category': 'at_risk',
        'flow_pattern': 'declining',
        'decline_reason': 'Board concerns about recent relative performance vs peers'
    },
    'metro_insurance': {
        'client_name': 'Metropolitan Insurance Group',
        'client_type': 'Insurance',
        'region': 'Europe',
        'aum_range': (120_000_000, 160_000_000),
        'priority': 11,
        'category': 'at_risk',
        'flow_pattern': 'declining',
        'decline_reason': 'New CIO conducting comprehensive manager review'
    },
    # --- New Clients (recently onboarded - for onboarding scenarios) ---
    'midwest_foundation': {
        'client_name': 'Midwest Community Foundation',
        'client_type': 'Foundation',
        'region': 'North America',
        'aum_range': (50_000_000, 75_000_000),
        'priority': 12,
        'category': 'new',
        'days_since_onboard': 45,
        'onboard_status': 'in_progress',
        'initial_allocation': 'SAM ESG Leaders Global Equity'
    },
    'nordic_family_office': {
        'client_name': 'Nordic Heritage Family Office',
        'client_type': 'Family Office',
        'region': 'Europe',
        'aum_range': (35_000_000, 50_000_000),
        'priority': 13,
        'category': 'new',
        'days_since_onboard': 21,
        'onboard_status': 'in_progress',
        'initial_allocation': 'SAM Global Thematic Growth'
    }
}

# #############################################################################
#
#                       END OF USER-EDITABLE SETTINGS
#
#  Settings below are advanced / internal. Only modify if you know what you
#  are doing.
#
# #############################################################################

# =============================================================================
# LOGGING & OUTPUT CONTROL (functions moved to logging_utils.py)
# =============================================================================
# Re-exported at end of file for backward compatibility


# =============================================================================
# MARKET_DATA SCHEMA CONFIGURATION (External Provider Data)
# =============================================================================

# This schema simulates data as received from a market data provider
# All tables follow provider-agnostic naming conventions
MARKET_DATA = {
    'enabled': True,
    'tables': {
        # Company & Security Master
        # Note: DIM_COMPANY has been eliminated - use CURATED.DIM_ISSUER directly
        'dim_security': 'DIM_SECURITY_PROVIDER',  # Provider's security master
        'dim_trading_item': 'DIM_TRADING_ITEM',
        'ref_exchange': 'REF_EXCHANGE',
        'ref_industry': 'REF_INDUSTRY',
        'ref_currency': 'REF_CURRENCY',
        'ref_country': 'REF_COUNTRY',
        
        # Financial Statements
        'fact_financial_period': 'FACT_FINANCIAL_PERIOD',
        'fact_financial_data': 'FACT_FINANCIAL_DATA',
        'fact_segment_financials': 'FACT_SEGMENT_FINANCIALS',
        'fact_debt_structure': 'FACT_DEBT_STRUCTURE',
        'fact_equity_structure': 'FACT_EQUITY_STRUCTURE',
        'ref_data_item': 'REF_DATA_ITEM',
        
        # Consensus & Analyst Data
        'fact_estimate_consensus': 'FACT_ESTIMATE_CONSENSUS',
        'fact_estimate_data': 'FACT_ESTIMATE_DATA',
        'fact_estimate_revision': 'FACT_ESTIMATE_REVISION',
        'dim_broker': 'DIM_BROKER',
        'dim_analyst': 'DIM_ANALYST',
        'fact_analyst_coverage': 'FACT_ANALYST_COVERAGE',
        
        # Filings (S&P Capital IQ pattern)
        'ref_filing_type': 'REF_FILING_TYPE',
        'ref_filing_source': 'REF_FILING_SOURCE',
        'ref_filing_language': 'REF_FILING_LANGUAGE',
        'ref_filing_institution_rel_type': 'REF_FILING_INSTITUTION_REL_TYPE',
        'fact_filing_ref': 'FACT_FILING_REF',
        'fact_filing_institution_rel': 'FACT_FILING_INSTITUTION_REL',
        'fact_filing_data': 'FACT_FILING_DATA'
    },
    'semantic_views': {
        'fundamentals': 'SAM_FUNDAMENTALS_VIEW',  # Financial statements + estimates
    },
    # Data generation settings (years_of_history wired to top-level YEARS_OF_HISTORY)
    'generation': {
        'years_of_history': YEARS_OF_HISTORY,
        'quarters_per_year': 4,
        'estimates_forward_years': 2,
        'brokers_per_company': (3, 8),  # Min/max broker coverage
        'revision_frequency': 0.3  # 30% of estimates get revised
    }
}

# Broker names for synthetic data
BROKER_NAMES = [
    'Goldman Sachs', 'Morgan Stanley', 'JPMorgan', 'Bank of America', 'Citigroup',
    'Barclays', 'Deutsche Bank', 'UBS', 'Credit Suisse', 'Wells Fargo',
    'RBC Capital', 'Jefferies', 'Piper Sandler', 'Baird', 'Stifel',
    'Raymond James', 'Cowen', 'Needham', 'Wedbush', 'Loop Capital'
]

# =============================================================================
# HELPER FUNCTIONS FOR DATABASE PATHS (moved to db_helpers.py)
# =============================================================================
# Re-exported at end of file for backward compatibility

# =============================================================================
# DATA MODEL CONFIGURATION
# =============================================================================

# Enhanced data model settings
DATA_MODEL = {
    'use_transaction_based': True,
    'generate_corporate_hierarchies': True,
    'issuer_hierarchy_depth': 2,
    'transaction_months': 12,
    'transaction_types': ['BUY', 'SELL', 'DIVIDEND', 'CORPORATE_ACTION'],
    'avg_monthly_transactions_per_security': 2.5,
    'portfolio_code_prefix': 'SAM',
    
    # =========================================================================
    # SYNTHETIC DATA DISTRIBUTIONS
    # Consolidated config for all data generation calibration parameters.
    # Used by sql_case_builders.py and config_accessors.py.
    # =========================================================================
    'synthetic_distributions': {
        # =====================================================================
        # SECTOR-BASED DISTRIBUTIONS
        # =====================================================================
        'by_sector': {
            'Information Technology': {
                'esg': {'E': (60, 95)},
                'factors': {
                    'Market': (0.9, 1.6),
                    'Value': (-1.0, 0.5),
                    'Growth': (0.5, 2.5),
                    'Quality': (0.5, 2.0),
                    'Volatility': (-0.1, 0.4)
                },
                'transaction_costs': {
                    'bid_ask_spread_bps': (3, 8),
                    'daily_volume_m': (2.0, 15.0),
                    'market_impact_bps_per_1m': (2, 6)
                }
            },
            'Utilities': {
                'esg': {'E': (20, 60)},
                'factors': {
                    'Market': (0.3, 0.7),
                    'Volatility': (-0.3, 0.1)
                },
                'transaction_costs': {
                    'bid_ask_spread_bps': (5, 12)
                }
            },
            'Energy': {
                'esg': {'E': (15, 50)},
                'factors': {
                    'Value': (0.5, 2.0),
                    'Growth': (-1.5, 0.3)
                },
                'transaction_costs': {
                    'bid_ask_spread_bps': (4, 10)
                }
            },
            'Health Care': {
                'factors': {
                    'Market': (0.6, 1.1),
                    'Growth': (0.3, 2.0),
                    'Quality': (0.3, 1.8)
                }
            },
            'Financials': {
                'factors': {
                    'Market': (0.8, 1.3),
                    'Value': (1.0, 2.5),
                    'Quality': (1.0, 2.5),
                    'Growth': (-0.5, 0.5)
                }
            },
            'Consumer Discretionary': {
                'factors': {
                    'Market': (0.9, 1.4),
                    'Value': (0.8, 2.2),
                    'Quality': (0.8, 2.2),
                    'Growth': (0.0, 1.5)
                }
            },
            'Industrials': {
                'factors': {
                    'Market': (0.8, 1.2),
                    'Value': (0.8, 2.2),
                    'Quality': (0.8, 2.2),
                    'Growth': (-0.3, 0.8)
                }
            },
            '_default': {
                'esg': {'E': (40, 80)},
                'factors': {
                    'Market': (0.7, 1.2),
                    'Value': (-0.5, 1.5),
                    'Growth': (-0.8, 1.0),
                    'Quality': (-0.5, 1.2),
                    'Volatility': (-0.2, 0.2)
                },
                'transaction_costs': {
                    'bid_ask_spread_bps': (4, 9),
                    'daily_volume_m': (0.5, 8.0),
                    'market_impact_bps_per_1m': (3, 8)
                }
            }
        },
        
        # =====================================================================
        # COUNTRY GROUP DISTRIBUTIONS
        # =====================================================================
        'country_groups': {
            'developed_americas': {
                'countries': ['US', 'CA'],
                'esg': {'S': (50, 85), 'G': (65, 95)},
                'settlement_days': 2
            },
            'developed_europe': {
                'countries': ['GB', 'DE', 'FR', 'SE', 'DK'],
                'esg': {'S': (60, 90), 'G': (65, 95)},
                'settlement_days': 2
            },
            '_default': {
                'esg': {'S': (45, 75), 'G': (40, 70)},
                'settlement_days': 3
            }
        },
        
        # =====================================================================
        # GLOBAL / STRATEGY / MISC DISTRIBUTIONS
        # =====================================================================
        'global': {
            # Factor model globals
            'factor_globals': {
                'Size': (-1.0, 1.5),
                'Momentum': (-1.5, 2.0)
            },
            'factor_r_squared': {
                'Market': 0.95, 'Size': 0.75, 'Value': 0.65,
                'Growth': 0.60, 'Momentum': 0.45, 'Quality': 0.55, 'Volatility': 0.35
            },
            
            # Transaction cost globals
            'transaction_cost_globals': {
                'commission_bps': (1, 3),
                'business_days_window': 66,
                'business_months_window': 3
            },
            
            # Strategy-based liquidity params
            'liquidity_by_strategy': {
                'Growth': {'liquidity_score': (7, 9), 'rebalancing_days': 90},
                'ESG': {'liquidity_score': (6, 8), 'rebalancing_days': 90},
                'Multi-Asset': {'liquidity_score': (5, 8), 'rebalancing_days': 30},
                '_default': {'liquidity_score': (5, 8), 'rebalancing_days': 60}
            },
            
            # Strategy-based risk limits
            'risk_limits_by_strategy': {
                'Growth': {'tracking_error_limit': (4.0, 6.0), 'max_sector_concentration': 0.50},
                'Multi-Asset': {'tracking_error_limit': (3.0, 5.0), 'max_sector_concentration': 0.35},
                '_default': {'tracking_error_limit': (2.0, 4.0), 'max_sector_concentration': 0.40}
            },
            
            # Global risk ranges
            'risk_globals': {
                'current_tracking_error_pct': (2.5, 4.8),
                'risk_budget_utilization_pct': (65, 85),
                'var_limit_1day_pct': (1.5, 3.0)
            },
            
            # Calendar/event frequencies
            'calendar': {
                'earnings_frequency_days': 90,
                'monthly_review_frequency_days': 30,
                'weekly_review_frequency_days': 7,
                'vix_range': (12, 35),
                'options_expiration_frequency_days': 21
            },
            
            # Tax parameters
            'tax': {
                'cost_basis_multiplier_range': (0.70, 1.30),
                'holding_period_days_range': (30, 1095),
                'long_term_threshold_days': 365,
                'long_term_rate': 0.20,
                'short_term_rate': 0.37,
                'tax_loss_harvest_threshold_usd': -10000
            },
            
            # Corporate action parameters
            'corporate_actions': {
                'dividend_range_usd': (0.50, 2.00),
                'action_type_weights': {'Dividend': 0.90, 'Split': 0.07, 'Merger': 0.03},
                'quarterly_event_frequency_days': 90,
                'ex_date_offset_days': 15,
                'record_date_offset_days': 16,
                'payment_date_offset_days': 30
            },
            
            # Client mandate defaults
            'client_mandates': {
                'approval_thresholds': {
                    'Flagship': 0.03,
                    'ESG': 0.04,
                    '_default': 0.05
                },
                'sector_allocation_defaults': {
                    'Technology': {'Technology': [0.30, 0.50], 'Healthcare': [0.05, 0.15]},
                    'ESG': {'Technology': [0.15, 0.35], 'Energy': [0.00, 0.05]},
                    '_default': {'Technology': [0.10, 0.40], 'Healthcare': [0.05, 0.20]}
                }
            },
            
            # Cash/liquidity globals
            'cash': {
                'cash_position_range_usd': (1_000_000, 25_000_000),
                'net_cashflow_30d_range_usd': (-5_000_000, 10_000_000)
            },
            
            # Client generation parameters
            'client': {
                # Total clients to generate (demo clients + generated)
                'total_count': 75,
                'total_count_test_mode': 10,
                
                # Generated client AUM range
                'aum_range_usd': (50_000_000, 500_000_000),
                
                # Relationship tenure for generated clients (days)
                'tenure_days_range': (365, 2920),  # 1-8 years
                
                # Demo client tenure formula: base + (max_priority - priority) * multiplier
                'demo_tenure_base_days': 365,
                'demo_tenure_multiplier_days': 150,
                
                # Generated client distribution weights (for MOD-based assignment)
                'client_types': ['Pension', 'Endowment', 'Foundation', 'Insurance', 'Corporate', 'Family Office'],
                'regions': ['North America', 'Europe', 'Asia Pacific', 'Middle East', 'Latin America'],
                
                # Primary contacts for client assignments
                'primary_contacts': [
                    'Sarah Chen', "Michael O'Brien", 'Jennifer Martinez', 'David Kim',
                    'Emma Thompson', 'Robert Singh', 'Lisa Anderson', 'James Wilson',
                    'Thomas Wright', 'Rachel Green', 'Christopher Lee', 'Amanda Foster', 'Daniel Park'
                ],
                
                # Generated client name patterns (for non-demo clients)
                # Used with " NNN" suffix, e.g. "State Teachers Retirement System 014"
                'generated_name_patterns': [
                    'State Teachers Retirement System',
                    'University Endowment Fund',
                    'Corporate Pension Trust',
                    'Healthcare Workers Pension',
                    'Municipal Employees Retirement',
                    'Private Foundation Trust',
                    'Insurance General Account',
                    'Family Office Holdings',
                    'Sovereign Wealth Reserve',
                    'Corporate Treasury Fund',
                    'Public Employees Pension',
                    'Charitable Foundation',
                    'Life Insurance Portfolio',
                    'Multi-Family Office',
                    'Institutional Investor'
                ]
            },
            
            # Client flow generation parameters  
            'client_flows': {
                'months_of_history': 12,
                
                # Standard client flow pattern (net positive)
                'standard_subscription_pct': 75,
                'standard_redemption_pct': 20,  # Remaining 5% is transfers
                
                # At-risk client flow pattern (net negative)
                'at_risk_redemption_pct': 80,
                
                # Client-portfolio allocation
                'allocation_weight_range': (0.3, 1.0),
                'single_product_pct': 20,   # ~20% have single portfolio
                'dual_product_pct': 30,     # ~30% have two portfolios
                # Remaining 50% have three portfolios
                
                # Flow amount as percentage of AUM
                'flow_amount_pct_range': (0.01, 0.05),
                
                # Strategy-specific flow multipliers
                'esg_recent_inflow_multiplier': 1.5,
                'esg_recent_months': 6,
                'growth_volatility_range': (0.8, 1.2),
                
                # Monthly flow probability (not every client has flow every month)
                'monthly_flow_probability_pct': 40
            }
        }
    }
}

# =============================================================================
# REAL DATA SOURCES - TABLE CATALOGUE
# =============================================================================
#
# This dict is attached to REAL_DATA_SOURCES['tables'] at module load time.
# It describes available tables in the external public data share.
#
REAL_DATA_SOURCES_TABLES = {
        # =============================================================================
        # COMPANY DATA (reference only - not used for DIM_SECURITY with DEMO_COMPANIES approach)
        # =============================================================================
        'openfigi_security_index': {
            'table': 'OPENFIGI_SECURITY_INDEX',
            'description': 'Security master data with tickers, FIGI identifiers, and exchange info',
            'key_columns': ['TOP_LEVEL_OPENFIGI_ID', 'PRIMARY_TICKER', 'SECURITY_NAME', 'ASSET_CATEGORY'],
            'coverage': 'Global securities with OpenFIGI identifiers',
            'replaces': None,
            'used_by': []  # No longer used - DIM_SECURITY derives from DIM_ISSUER directly
        },
        'company_security_relationships': {
            'table': 'COMPANY_SECURITY_RELATIONSHIPS',
            'description': 'Links companies to their securities',
            'key_columns': ['COMPANY_ID', 'SECURITY_ID', 'SECURITY_ID_TYPE'],
            'coverage': 'Company-security mappings',
            'replaces': None,
            'used_by': []  # No longer used with DEMO_COMPANIES approach
        },
        'company_characteristics': {
            'table': 'COMPANY_CHARACTERISTICS',
            'description': 'Company attributes including country, SIC codes, addresses',
            'key_columns': ['COMPANY_ID', 'RELATIONSHIP_TYPE', 'VALUE'],
            'coverage': 'Company metadata and characteristics',
            'replaces': None,
            'used_by': ['generate_structured.py (DIM_ISSUER enrichment)']
        },
        # =============================================================================
        # COMPANY INDEX (shared by multiple modules)
        # =============================================================================
        'company_index': {
            'table': 'COMPANY_INDEX',
            'description': 'Company master data with CIK, EIN, LEI identifiers',
            'key_columns': ['COMPANY_ID', 'COMPANY_NAME', 'CIK', 'EIN', 'LEI'],
            'coverage': 'US public companies',
            'replaces': None,  # DIM_COMPANY has been eliminated - DIM_ISSUER is single source of truth
            'used_by': ['generate_structured.py (DIM_ISSUER enrichment)']
        },
        # =============================================================================
        # STOCK PRICE DATA
        # =============================================================================
        'stock_prices': {
            'table': 'STOCK_PRICE_TIMESERIES',
            'description': 'Daily open/close prices, high/low prices, and trading volumes for US securities traded on Nasdaq',
            'key_columns': ['TICKER', 'DATE', 'VARIABLE', 'VALUE'],
            'coverage': 'US equities on Nasdaq',
            'replaces': 'FACT_MARKETDATA_TIMESERIES',
            'used_by': ['generate_market_data.py']
        },
        # =============================================================================
        # SEC FILING DATA
        # =============================================================================
        'sec_metrics': {
            'table': 'SEC_METRICS_TIMESERIES',
            'description': 'Quarterly and annual parsed revenue segments from 10-Qs and 10-Ks with geography and business segment breakdowns',
            'key_columns': ['COMPANY_ID', 'CIK', 'GEO_NAME', 'BUSINESS_SEGMENT', 'BUSINESS_SUBSEGMENT', 'CUSTOMER', 'LEGAL_ENTITY', 'FISCAL_YEAR', 'FISCAL_PERIOD', 'VALUE'],
            'coverage': 'US public companies with SEC filings - revenue segments only',
            'replaces': None,
            'used_by': ['generate_market_data.py (FACT_SEC_SEGMENTS)']
        },
        'sec_filing_text': {
            'table': 'SEC_REPORT_TEXT_ATTRIBUTES',
            'description': 'Full text of company filings (10-Ks, 10-Qs, 8-Ks) submitted to the SEC',
            'key_columns': ['SEC_DOCUMENT_ID', 'CIK', 'ADSH', 'VARIABLE', 'VARIABLE_NAME', 'PERIOD_END_DATE', 'VALUE'],
            'coverage': 'SEC filings text content',
            'replaces': 'FACT_FILING_DATA',
            'used_by': ['generate_market_data.py']
        },
        'sec_corporate_financials': {
            'table': 'SEC_CORPORATE_REPORT_ATTRIBUTES',
            'description': 'Full SEC financial statements (Income Statement, Balance Sheet, Cash Flow) with XBRL tags',
            'key_columns': ['CIK', 'ADSH', 'TAG', 'STATEMENT', 'PERIOD_END_DATE', 'VALUE', 'MEASURE_DESCRIPTION'],
            'coverage': '569M records across 17,258 companies - complete financial statements',
            'replaces': 'FACT_FINANCIAL_DATA (supplements with real data)',
            'used_by': ['generate_market_data.py']
        },
        'sec_report_attributes': {
            'table': 'SEC_REPORT_ATTRIBUTES',
            'description': 'SEC report metadata including form type, filing dates',
            'key_columns': ['ADSH', 'CIK', 'FORM_TYPE', 'FILED_DATE'],
            'coverage': 'SEC filing metadata',
            'replaces': None,
            'used_by': ['generate_structured.py']
        },
        'sec_report_index': {
            'table': 'SEC_REPORT_INDEX',
            'description': 'Index of SEC reports with filing URLs',
            'key_columns': ['ADSH', 'CIK'],
            'coverage': 'SEC filing index',
            'replaces': None,
            'used_by': ['generate_structured.py']
        },
        'sec_fiscal_calendars': {
            'table': 'SEC_FISCAL_CALENDARS',
            'description': 'Fiscal calendar data for SEC filers',
            'key_columns': ['CIK', 'FISCAL_YEAR', 'FISCAL_PERIOD', 'PERIOD_END_DATE'],
            'coverage': 'Fiscal period information',
            'replaces': None,
            'used_by': ['hydration_engine.py']
        },
        # =============================================================================
        # INSTITUTIONAL HOLDINGS
        # =============================================================================
        'sec_13f': {
            'table': 'SEC_13F_ATTRIBUTES',
            'description': 'Institutional investment manager holdings from 13F filings',
            'key_columns': ['CIK', 'ADSH', 'CUSIP', 'SHARES', 'VALUE'],
            'coverage': 'Institutional holdings data',
            'replaces': None,
            'used_by': []  # Future use
        },
        # =============================================================================
        # COMPANY EVENT TRANSCRIPTS (Earnings Calls, AGMs, Investor Days, etc.)
        # =============================================================================
        'company_event_transcripts': {
            'table': 'COMPANY_EVENT_TRANSCRIPT_ATTRIBUTES',
            'description': 'Transcripts of hosted company events (Earnings Calls, AGMs, M&A, Investor Days) in JSON format',
            'key_columns': ['COMPANY_ID', 'CIK', 'PRIMARY_TICKER', 'EVENT_TYPE', 'EVENT_TIMESTAMP', 'TRANSCRIPT'],
            'coverage': '9000+ public companies with varying history',
            'replaces': 'CURATED.EARNINGS_TRANSCRIPTS_CORPUS (synthetic)',
            'used_by': ['generate_real_transcripts.py']
        }
    }

# Attach the table catalogue to REAL_DATA_SOURCES for compatibility
REAL_DATA_SOURCES['tables'] = REAL_DATA_SOURCES_TABLES

# Helper function for test mode counts
# =============================================================================
# COMPLIANCE & RISK CONFIGURATION
# =============================================================================

COMPLIANCE_RULES = {
    'concentration': {
        'max_single_issuer': 0.07,     # 7%
        'warning_threshold': 0.065,    # 6.5%
        'tech_portfolio_max': 0.065    # 6.5% for technology portfolios
    },
    'fi_guardrails': {
        'min_investment_grade': 0.75,  # 75%
        'max_ccc_below': 0.05,         # 5%
        'duration_tolerance': 1.0      # ±1.0 years vs benchmark
    },
    'esg': {
        'min_overall_rating': 'BBB',
        'exclude_high_controversy': True,
        'applicable_portfolios': ['SAM ESG Leaders Global Equity', 'SAM Renewable & Climate Solutions'],
        # ESG grading configuration (for build_esg_scores)
        'grade_thresholds': [(86, 'AAA'), (71, 'AA'), (57, 'A'), (43, 'BBB'), (29, 'BB'), (14, 'B')],
        'default_grade': 'CCC',
        'default_provider': 'MSCI',
        'overall_weights': {'E': 1.0, 'S': 1.0, 'G': 1.0}  # Relative weights (1:1:1 = equal)
    }
}

# =============================================================================
# PORTFOLIO CONFIGURATION
# =============================================================================

# Demo portfolios that get special document coverage
DEMO_PORTFOLIOS_WITH_DOCS = [
    'SAM Technology & Infrastructure',
    'SAM Global Thematic Growth',
    'SAM Multi-Asset Income',
    'SAM ESG Leaders Global Equity'
]

# Default demo portfolio for examples
DEFAULT_DEMO_PORTFOLIO = 'SAM Technology & Infrastructure'

PORTFOLIOS = {
    'SAM Technology & Infrastructure': {
        'benchmark': 'Nasdaq 100',
        'aum_usd': 1.5e9,
        'strategy': 'Growth',
        'inception_date': '2019-01-01',
        'base_currency': 'USD',
        'is_demo_portfolio': True,
        # Priority holdings and position sizes now defined in DEMO_COMPANIES (demo_order, position_size)
        'filler_holdings': 'tech_stocks',
        'target_position_count': 45
    },
    'SAM Global Flagship Multi-Asset': {
        'benchmark': 'MSCI ACWI',
        'aum_usd': 2.5e9,
        'strategy': 'Multi-Asset',
        'inception_date': '2019-01-01',
        'base_currency': 'USD'
    },
    'SAM ESG Leaders Global Equity': {
        'benchmark': 'MSCI ACWI',
        'aum_usd': 1.8e9,
        'strategy': 'ESG',
        'inception_date': '2019-01-01',
        'base_currency': 'USD'
    },
    'SAM US Core Equity': {
        'benchmark': 'S&P 500',
        'aum_usd': 1.2e9,
        'strategy': 'Core',
        'inception_date': '2019-01-01',
        'base_currency': 'USD'
    },
    'SAM Renewable & Climate Solutions': {
        'benchmark': 'Nasdaq 100',
        'aum_usd': 1.0e9,
        'strategy': 'ESG',
        'inception_date': '2019-01-01',
        'base_currency': 'USD'
    },
    'SAM Sustainable Global Equity': {
        'benchmark': 'MSCI ACWI',
        'aum_usd': 1.1e9,
        'strategy': 'ESG',
        'inception_date': '2019-01-01',
        'base_currency': 'USD'
    },
    'SAM AI & Digital Innovation': {
        'benchmark': 'Nasdaq 100',
        'aum_usd': 0.9e9,
        'strategy': 'Growth',
        'inception_date': '2019-01-01',
        'base_currency': 'USD'
    },
    'SAM Global Balanced 60/40': {
        'benchmark': 'MSCI ACWI',
        'aum_usd': 0.8e9,
        'strategy': 'Multi-Asset',
        'inception_date': '2019-01-01',
        'base_currency': 'USD'
    },
    'SAM Tech Disruptors Equity': {
        'benchmark': 'Nasdaq 100',
        'aum_usd': 0.7e9,
        'strategy': 'Growth',
        'inception_date': '2019-01-01',
        'base_currency': 'USD'
    },
    'SAM US Value Equity': {
        'benchmark': 'S&P 500',
        'aum_usd': 0.6e9,
        'strategy': 'Value',
        'inception_date': '2019-01-01',
        'base_currency': 'USD'
    },
    'SAM Multi-Asset Income': {
        'benchmark': 'S&P 500',
        'aum_usd': 0.5e9,
        'strategy': 'Income',
        'inception_date': '2019-01-01',
        'base_currency': 'USD'
    }
}

# =============================================================================
# MANDATE COMPLIANCE CONFIGURATION (for Scenario 3.2)
# =============================================================================

# Mandate compliance demo scenario configuration
SCENARIO_3_2_MANDATE_COMPLIANCE = {
    'portfolio': 'SAM AI & Digital Innovation',
    'non_compliant_holding': {
        'ticker': 'META',
        'issue': 'ESG_DOWNGRADE',
        'original_esg_grade': 'A',
        'downgraded_esg_grade': 'CCC',
        'reason': 'Governance concerns related to data privacy practices and content moderation',
        'action_deadline_days': 30  # Days from alert to resolution deadline
    },
    'pre_screened_replacements': [
        {
            'ticker': 'NVDA',
            'rank': 1,
            'ai_growth_score': 92,
            'esg_grade': 'A',
            'market_cap_b': 1200,
            'liquidity_score': 10,
            'rationale': 'Leader in AI compute infrastructure with dominant data center GPU market share, strong ESG governance, and robust patent portfolio in machine learning accelerators'
        },
        {
            'ticker': 'MSFT',
            'rank': 2,
            'ai_growth_score': 89,
            'esg_grade': 'A',
            'market_cap_b': 2800,
            'liquidity_score': 10,
            'rationale': 'Azure AI platform leader with OpenAI partnership, excellent ESG track record, and significant investment in responsible AI development'
        },
        {
            'ticker': 'GOOGL',
            'rank': 3,
            'ai_growth_score': 85,
            'esg_grade': 'A',
            'market_cap_b': 1700,
            'liquidity_score': 10,
            'rationale': 'AI research leader with DeepMind and Google Brain, solid ESG performance though some historical privacy concerns addressed'
        }
    ],
    'mandate_requirements': {
        'min_esg_grade': 'A',
        'max_concentration': 0.065,  # 6.5% for this portfolio
        'required_sector': 'Information Technology',
        'ai_growth_threshold': 80,
        'min_market_cap_b': 50,
        'min_liquidity_score': 7
    }
}

# =============================================================================
# ESG DEMO OVERRIDES (for ESG Rating Monitor scenario)
# =============================================================================

# Securities with intentionally low ESG scores for demo scenarios
# These create holdings below the BBB threshold in ESG-labelled portfolios
# to demonstrate breach detection and remediation workflows
ESG_DEMO_OVERRIDES = {
    # Securities that should have BB grade (score 29-42) for demo scenarios
    'INTC': {
        'ticker': 'INTC',
        'esg_grade': 'BB',
        'esg_score': 35,  # Score in BB range (29-42)
        'reason': 'Environmental concerns - manufacturing emissions'
    },
    'IBM': {
        'ticker': 'IBM',
        'esg_grade': 'BB',
        'esg_score': 38,  # Score in BB range (29-42)
        'reason': 'Governance concerns - board diversity'
    },
    # Securities that should have B grade (score 14-28) for demo scenarios
    'CSCO': {
        'ticker': 'CSCO',
        'esg_grade': 'B',
        'esg_score': 22,  # Score in B range (14-28)
        'reason': 'Social concerns - supply chain labor practices'
    },
    # Securities that should have CCC grade (score 0-13) for demo scenarios
    'META': {
        'ticker': 'META',
        'esg_grade': 'CCC',
        'esg_score': 10,  # Score in CCC range (0-13)
        'reason': 'Governance concerns - data privacy practices and content moderation'
    },
}

# =============================================================================
# SUPPLY CHAIN CONFIGURATION (for Risk Verification scenario)
# =============================================================================

# Supply chain relationship patterns for demo scenario
# NOTE: Companies (TSM, NVDA, AMD, AAPL, GM, F) are now in DEMO_COMPANIES
# Format: (Company, Counterparty, RelationshipType, CostShare/RevenueShare, CriticalityTier)
SUPPLY_CHAIN_DEMO_RELATIONSHIPS = [
    # Taiwan semiconductor → US tech companies (high dependency)
    ('TSM', 'NVDA', 'Customer', 0.25, 'High'),      # NVDA gets 25% revenue from TSM
    ('TSM', 'AMD', 'Customer', 0.18, 'High'),       # AMD gets 18% revenue from TSM
    ('TSM', 'AAPL', 'Customer', 0.30, 'High'),      # AAPL gets 30% revenue from TSM
    
    # US tech companies → automotive (medium dependency)
    ('NVDA', 'GM', 'Customer', 0.08, 'Medium'),     # GM gets 8% chips from NVDA
    ('NVDA', 'F', 'Customer', 0.06, 'Medium'),      # Ford gets 6% chips from NVDA
    ('AMD', 'GM', 'Customer', 0.05, 'Medium'),      # GM gets 5% chips from AMD
]

# Relationship strength ranges by industry
SUPPLY_CHAIN_RELATIONSHIP_STRENGTHS = {
    'semiconductors': {
        'critical_suppliers_share': (0.20, 0.40),   # 20-40% per critical supplier
        'major_customers_share': (0.15, 0.30),      # 15-30% per major customer
        'relationship_count_range': (5, 10)          # 5-10 relationships per company
    },
    'automotive': {
        'critical_suppliers_share': (0.10, 0.20),
        'major_customers_share': (0.08, 0.15),
        'relationship_count_range': (3, 5)
    },
    'technology': {
        'critical_suppliers_share': (0.15, 0.30),
        'major_customers_share': (0.10, 0.25),
        'relationship_count_range': (4, 8)
    },
    'default': {
        'critical_suppliers_share': (0.05, 0.15),
        'major_customers_share': (0.05, 0.12),
        'relationship_count_range': (1, 3)
    }
}

# =============================================================================
# SCENARIO & AGENT CONFIGURATION
# =============================================================================

AVAILABLE_SCENARIOS = [
    'portfolio_copilot',
    'research_copilot',
    'thematic_macro_advisor',
    'esg_guardian',
    'sales_advisor',
    'quant_analyst',
    'compliance_advisor',
    'middle_office_copilot',
    'executive_copilot'
]

# Scenario to agent mapping with descriptions
SCENARIO_AGENTS = {
    'portfolio_copilot': {
        'agent_name': 'AM_portfolio_copilot',
        'display_name': 'Portfolio Co-Pilot',
        'description': 'Portfolio analytics and benchmarking'
    },
    'research_copilot': {
        'agent_name': 'AM_research_copilot',
        'display_name': 'Research Co-Pilot',
        'description': 'Document research and analysis'
    },
    'thematic_macro_advisor': {
        'agent_name': 'AM_thematic_macro_advisor',
        'display_name': 'Thematic Macro Advisor',
        'description': 'Thematic investment strategy'
    },
    'esg_guardian': {
        'agent_name': 'AM_esg_guardian',
        'display_name': 'ESG Guardian',
        'description': 'ESG risk monitoring'
    },
    'compliance_advisor': {
        'agent_name': 'AM_compliance_advisor',
        'display_name': 'Compliance Advisor',
        'description': 'Mandate monitoring'
    },
    'sales_advisor': {
        'agent_name': 'AM_sales_advisor',
        'display_name': 'Sales Advisor',
        'description': 'Client reporting'
    },
    'quant_analyst': {
        'agent_name': 'AM_quant_analyst',
        'display_name': 'Quant Analyst',
        'description': 'Factor analysis'
    },
    'middle_office_copilot': {
        'agent_name': 'AM_middle_office_copilot',
        'display_name': 'Middle Office Co-Pilot',
        'description': 'Operations monitoring and NAV calculation'
    },
    'executive_copilot': {
        'agent_name': 'AM_executive_copilot',
        'display_name': 'Executive Command Center',
        'description': 'Firm-wide KPIs, client analytics, and strategic M&A analysis'
    }
}

SCENARIO_DATA_REQUIREMENTS = {
    'portfolio_copilot': ['broker_research', 'company_event_transcripts', 'press_releases', 'macro_events', 'report_templates'],
    'research_copilot': ['broker_research', 'company_event_transcripts'],
    'thematic_macro_advisor': ['broker_research', 'press_releases', 'company_event_transcripts'],
    'esg_guardian': ['ngo_reports', 'engagement_notes', 'policy_docs'],
    'sales_advisor': ['sales_templates', 'philosophy_docs', 'policy_docs'],
    'quant_analyst': ['broker_research', 'company_event_transcripts'],
    'compliance_advisor': ['policy_docs', 'engagement_notes'],
    'middle_office_copilot': ['custodian_reports', 'reconciliation_notes', 'ssi_documents', 'ops_procedures'],
    'mandate_compliance': ['report_templates'],  # Alias for portfolio_copilot mandate compliance mode
    'executive_copilot': ['strategy_documents', 'press_releases', 'broker_research']  # Executive leadership scenario
}

# =============================================================================
# DOCUMENT GENERATION CONFIGURATION
# =============================================================================

# Paths
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CONFIG_DIR)
CONTENT_LIBRARY_PATH = os.path.join(PROJECT_ROOT, 'content_library')
CONTENT_VERSION = '1.0'

# =============================================================================
# SECTOR MAPPING CONFIGURATION (for template selection)
# =============================================================================

# Map SIC industry descriptions to GICS sectors for template matching
SIC_TO_GICS_MAPPING = {
    'Information Technology': [
        'software', 'computer programming', 'prepackaged software', 'data processing',
        'computer systems design', 'information retrieval', 'computer facilities',
        'semiconductors', 'electronic computers', 'computer peripheral',
        'computer integrated systems', 'computer storage devices', 'computer terminals'
    ],
    'Health Care': [
        'pharmaceutical', 'drugs', 'medicinal', 'biological', 'medical',
        'hospital', 'health', 'diagnostic', 'surgical', 'dental',
        'biotechnology', 'medical instruments', 'medical laboratories'
    ],
    'Consumer Discretionary': [
        'retail', 'automobile', 'motor vehicle', 'apparel', 'restaurant',
        'hotel', 'broadcasting', 'cable', 'media', 'entertainment', 'leisure',
        'department store', 'specialty retail', 'home furnishing'
    ],
    'Financials': [
        'bank', 'insurance', 'investment', 'securities', 'credit',
        'finance', 'real estate', 'mortgage', 'savings institution',
        'asset management', 'capital markets'
    ],
    'Energy': [
        'oil', 'gas', 'petroleum', 'crude', 'coal', 'energy',
        'exploration', 'drilling', 'refining', 'pipeline'
    ],
    'Industrials': [
        'aerospace', 'defense', 'construction', 'machinery', 'equipment',
        'transportation', 'airline', 'railroad', 'trucking', 'freight',
        'engineering', 'electrical equipment', 'industrial machinery'
    ],
    'Consumer Staples': [
        'food', 'beverage', 'tobacco', 'household products', 'personal products',
        'grocery', 'packaged foods', 'soft drinks'
    ],
    'Materials': [
        'chemicals', 'metals', 'mining', 'paper', 'packaging',
        'steel', 'aluminum', 'gold', 'silver', 'construction materials'
    ],
    'Utilities': [
        'electric', 'water', 'natural gas utility', 'power generation',
        'electric services', 'water supply'
    ],
    'Communication Services': [
        'telecommunications', 'wireless', 'internet services', 'social media',
        'telephone communications', 'cable television'
    ],
    'Real Estate': [
        'reit', 'real estate investment', 'property management',
        'real estate operating', 'real estate development'
    ]
}

DOCUMENT_TYPES = {
    'broker_research': {
        'table_name': 'BROKER_RESEARCH_RAW',
        'corpus_name': 'BROKER_RESEARCH_CORPUS',
        'search_service': 'SAM_BROKER_RESEARCH',
        'word_count_range': (700, 1200),
        'applies_to': 'securities',
        'linkage_level': 'security',
        'template_dir': 'security/broker_research',
        'variants_per_sector': 3,
        'coverage_count': 8
    },
    'company_event_transcripts': {
        'table_name': 'COMPANY_EVENT_TRANSCRIPTS_RAW',
        'corpus_name': 'COMPANY_EVENT_TRANSCRIPTS_CORPUS',
        'search_service': 'SAM_COMPANY_EVENTS',
        'word_count_range': (500, 2000),  # Per chunk after splitting
        'applies_to': 'securities',
        'linkage_level': 'security',
        'source': 'real',  # Indicates real data from SNOWFLAKE_PUBLIC_DATA_FREE
        'coverage_count': 31,  # Demo companies + major stocks + SNOW
        'event_types': ['Earnings Call', 'Update / Briefing', 'M&A Announcement', 
                        'Annual General Meeting', 'Investor / Analyst Day', 'Special Call'],
        'chunk_size_tokens': 512,
        'speaker_mapping_table': 'COMP_EVENT_SPEAKER_MAPPING'
    },
    'press_releases': {
        'table_name': 'PRESS_RELEASES_RAW',
        'corpus_name': 'PRESS_RELEASES_CORPUS',
        'search_service': 'SAM_PRESS_RELEASES',
        'word_count_range': (250, 400),
        'applies_to': 'securities',
        'linkage_level': 'security',
        'template_dir': 'security/press_releases',
        'variants_per_sector': 3,
        'coverage_count': 8,
        'releases_per_company': 4
    },
    'ngo_reports': {
        'table_name': 'NGO_REPORTS_RAW',
        'corpus_name': 'NGO_REPORTS_CORPUS',
        'search_service': 'SAM_NGO_REPORTS',
        'word_count_range': (400, 800),
        'applies_to': 'issuers',
        'linkage_level': 'issuer',
        'template_dir': 'issuer/ngo_reports',
        'categories': ['environmental', 'social', 'governance'],
        'severity_levels': ['high', 'medium', 'low'],
        'coverage_count': 8,
        'reports_per_company': 2
    },
    'engagement_notes': {
        'table_name': 'ENGAGEMENT_NOTES_RAW',
        'corpus_name': 'ENGAGEMENT_NOTES_CORPUS',
        'search_service': 'SAM_ENGAGEMENT_NOTES',
        'word_count_range': (150, 300),
        'applies_to': 'issuers',
        'linkage_level': 'issuer',
        'template_dir': 'issuer/engagement_notes',
        'meeting_types': ['management_meeting', 'shareholder_call', 'compliance_discussion'],
        'coverage_count': 8,
        'notes_per_company': 1
    },
    'policy_docs': {
        'table_name': 'POLICY_DOCS_RAW',
        'corpus_name': 'POLICY_DOCS_CORPUS',
        'search_service': 'SAM_POLICY_DOCS',
        'word_count_range': (800, 1500),
        'applies_to': None,
        'linkage_level': 'global',
        'template_dir': 'global/policy_docs',
        'policy_types': [
            'concentration_risk_policy',
            'sustainable_investment_policy',
            'investment_management_agreement'
        ],
        'docs_total': 3
    },
    'sales_templates': {
        'table_name': 'SALES_TEMPLATES_RAW',
        'corpus_name': 'SALES_TEMPLATES_CORPUS',
        'search_service': 'SAM_SALES_TEMPLATES',
        'word_count_range': (800, 1500),
        'applies_to': None,
        'linkage_level': 'global',
        'template_dir': 'global/sales_templates',
        'template_types': [
            'monthly_client_report', 
            'quarterly_client_letter',
            'rfp_response_template',
            'client_onboarding_welcome',
            'client_retention_playbook',
            'product_catalog'
        ],
        'docs_total': 6
    },
    'philosophy_docs': {
        'table_name': 'PHILOSOPHY_DOCS_RAW',
        'corpus_name': 'PHILOSOPHY_DOCS_CORPUS',
        'search_service': 'SAM_PHILOSOPHY_DOCS',
        'word_count_range': (800, 1500),
        'applies_to': None,
        'linkage_level': 'global',
        'template_dir': 'global/philosophy_docs',
        'philosophy_types': ['esg_philosophy', 'risk_philosophy', 'brand_guidelines'],
        'docs_total': 3
    },
    'report_templates': {
        'table_name': 'REPORT_TEMPLATES_RAW',
        'corpus_name': 'REPORT_TEMPLATES_CORPUS',
        'search_service': 'SAM_REPORT_TEMPLATES',
        'word_count_range': (1500, 2500),
        'applies_to': None,
        'linkage_level': 'global',
        'template_dir': 'global/report_templates',
        'template_types': [
            'mandate_compliance_standard',
            'esg_committee_report',
            'risk_committee_compliance_report'
        ],
        'docs_total': 4
    },
    'macro_events': {
        'table_name': 'MACRO_EVENTS_RAW',
        'corpus_name': 'MACRO_EVENTS_CORPUS',
        'search_service': 'SAM_MACRO_EVENTS',
        'word_count_range': (400, 800),
        'applies_to': None,
        'linkage_level': 'global',
        'template_dir': 'global/macro_events',
        'event_types': ['NaturalDisaster', 'Geopolitical', 'RegulatoryShock', 'CyberIncident', 'SupplyDisruption'],
        'regions': ['TW', 'US', 'CN', 'EU', 'JP'],
        'severity_levels': ['Low', 'Medium', 'High', 'Critical'],
        'affected_sectors': ['Information Technology', 'Consumer Discretionary', 'Industrials', 'Materials'],
        'docs_total': 1,  # Single Taiwan earthquake event for demo
        'demo_event': {
            'event_type': 'NaturalDisaster',
            'region': 'TW',
            'severity': 'Critical',
            'affected_sectors': ['Information Technology', 'Consumer Discretionary'],
            'title': 'Major Earthquake Disrupts Taiwan Semiconductor Production',
            'impact_description': 'A 7.2 magnitude earthquake has struck central Taiwan, affecting major semiconductor manufacturing facilities including TSMC fabs. Production halts expected for 2-4 weeks with downstream supply chain impacts on global technology and automotive sectors.'
        }
    },
    'custodian_reports': {
        'table_name': 'CUSTODIAN_REPORTS_RAW',
        'corpus_name': 'CUSTODIAN_REPORTS_CORPUS',
        'search_service': 'SAM_CUSTODIAN_REPORTS',
        'word_count_range': (500, 800),
        'applies_to': 'portfolios',
        'linkage_level': 'portfolio',
        'template_dir': 'portfolio/custodian_reports',
        'report_types': ['daily_holdings', 'cash_statement', 'transaction_summary'],
        'portfolios': DEMO_PORTFOLIOS_WITH_DOCS,
        'docs_per_portfolio': 3
    },
    'reconciliation_notes': {
        'table_name': 'RECONCILIATION_NOTES_RAW',
        'corpus_name': 'RECONCILIATION_NOTES_CORPUS',
        'search_service': 'SAM_RECONCILIATION_NOTES',
        'word_count_range': (200, 400),
        'applies_to': None,
        'linkage_level': 'global',
        'template_dir': 'global/reconciliation_notes',
        'break_types': ['position_break', 'cash_break', 'price_break', 'corporate_action_break'],
        'docs_total': 8
    },
    'ssi_documents': {
        'table_name': 'SSI_DOCUMENTS_RAW',
        'corpus_name': 'SSI_DOCUMENTS_CORPUS',
        'search_service': 'SAM_SSI_DOCUMENTS',
        'word_count_range': (300, 600),
        'applies_to': None,
        'linkage_level': 'global',
        'template_dir': 'global/ssi_documents',
        'instruction_types': ['equity_settlement', 'fx_settlement', 'bond_settlement'],
        'docs_total': 6
    },
    'ops_procedures': {
        'table_name': 'OPS_PROCEDURES_RAW',
        'corpus_name': 'OPS_PROCEDURES_CORPUS',
        'search_service': 'SAM_OPS_PROCEDURES',
        'word_count_range': (800, 1500),
        'applies_to': None,
        'linkage_level': 'global',
        'template_dir': 'global/ops_procedures',
        'procedure_types': ['settlement_failure_resolution', 'nav_calculation_process', 'reconciliation_workflow'],
        'docs_total': 3
    },
    'strategy_documents': {
        'table_name': 'STRATEGY_DOCUMENTS_RAW',
        'corpus_name': 'STRATEGY_DOCUMENTS_CORPUS',
        'search_service': 'SAM_STRATEGY_DOCUMENTS',
        'word_count_range': (1100, 1400),
        'applies_to': None,
        'linkage_level': 'global',
        'template_dir': 'global/strategy_documents',
        'document_types': ['strategic_planning_presentation', 'board_meeting_summary'],
        'docs_total': 2
    }
}

# =============================================================================
# MARKET & REFERENCE DATA CONFIGURATION
# =============================================================================

BENCHMARKS = [
    {
        'id': 'SP500',
        'name': 'S&P 500',
        'currency': 'USD',
        'provider': 'PLM',
        'holdings_rules': {
            'constituent_count': 500,
            'filters': {'country': 'US'},
            'raw_weight_range': (0.001, 0.07),
            'min_weight': 0.0001,
            'assumed_benchmark_mv_usd': 1_000_000_000
        }
    },
    {
        'id': 'MSCI_ACWI',
        'name': 'MSCI ACWI',
        'currency': 'USD',
        'provider': 'NSD',
        'holdings_rules': {
            'constituent_count': 800,
            'filters': {'all': True},  # No country filter
            'weight_by_country': {     # Country-differentiated weights
                'US': (0.001, 0.05),
                '_default': (0.0001, 0.01)
            },
            'min_weight': 0.0001,
            'assumed_benchmark_mv_usd': 1_000_000_000
        }
    },
    {
        'id': 'NASDAQ100',
        'name': 'Nasdaq 100',
        'currency': 'USD',
        'provider': 'PLM',
        'holdings_rules': {
            'constituent_count': 100,
            'filters': {'sector': 'Information Technology'},
            'raw_weight_range': (0.005, 0.12),
            'min_weight': 0.0001,
            'assumed_benchmark_mv_usd': 1_000_000_000
        }
    }
]

# Data distribution
DATA_DISTRIBUTION = {
    'regions': {'US': 0.55, 'Europe': 0.30, 'APAC_EM': 0.15},
    'asset_classes': {'equities': 1.0},  # Equities only with new DEMO_COMPANIES approach
}

# Currency & Calendar
BASE_CURRENCY = 'USD'
SUPPORTED_CURRENCIES = ['USD', 'EUR', 'GBP']
FX_HEDGING = 'FULLY_HEDGED'
TRADING_CALENDAR = 'UTC_BUSINESS_DAYS'
RETURNS_FREQUENCY = 'MONTHLY'

# =============================================================================
# CONTENT GENERATION CONFIGURATION
# =============================================================================

# ESG Controversy Keywords
ESG_CONTROVERSY_KEYWORDS = {
    'environmental': {
        'high': ['toxic spill', 'environmental disaster', 'illegal dumping', 'major pollution'],
        'medium': ['environmental violation', 'emissions breach', 'waste management'],
        'low': ['environmental concern', 'sustainability question']
    },
    'social': {
        'high': ['forced labor', 'child labor', 'human rights violation', 'workplace fatality'],
        'medium': ['labor dispute', 'workplace injury', 'discrimination allegation'],
        'low': ['employee concern', 'workplace issue']
    },
    'governance': {
        'high': ['fraud investigation', 'criminal charges', 'regulatory sanction'],
        'medium': ['accounting irregularity', 'governance breach', 'compliance violation'],
        'low': ['governance concern', 'board dispute']
    }
}

# Fictional provider names
FICTIONAL_BROKER_NAMES = [
    'Ashfield Partners', 'Northgate Analytics', 'Blackstone Ridge Research',
    'Fairmont Capital Insights', 'Kingswell Securities Research',
    'Brookline Advisory Group', 'Harrow Street Markets', 'Marlowe & Co. Research',
    'Crescent Point Analytics', 'Simulated Wharf Intelligence', 'Granite Peak Advisory',
    'Alder & Finch Investments', 'Bluehaven Capital Research', 'Regent Square Analytics',
    'Whitestone Equity Research'
]

FICTIONAL_NGO_NAMES = {
    'environmental': [
        'Global Sustainability Watch', 'Environmental Justice Initiative',
        'Climate Action Network', 'Green Future Alliance'
    ],
    'social': [
        'Human Rights Monitor', 'Labour Rights Observatory',
        'Ethical Investment Coalition', 'Fair Workplace Institute'
    ],
    'governance': [
        'Corporate Accountability Forum', 'Transparency Advocacy Group',
        'Corporate Responsibility Institute', 'Ethical Governance Council'
    ]
}

# =============================================================================
# END OF CONFIGURATION
# =============================================================================
