import os
import sqlite3
from Config.config import *
import subprocess
import time
import socket
import requests
from time import sleep

DB_PATH = "stockDB.db"


def wait_for_port(host, port, timeout=30, interval=0.5):
    start_time = time.time()
    while True:
        try:
            with socket.create_connection((host, port), timeout=2):
                print(f"Port {port} is open on {host}")
                return True
        except (ConnectionRefusedError, socket.timeout):
            if time.time() - start_time > timeout:
                print(f"Timeout: Port {port} not open after {timeout} seconds.")
                return False
            time.sleep(interval)

def get_jwt_token():
    response = requests.post(Config.LOGIN_URL, json={'api_key': Config.DATA_APP_API_KEY})
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception('Failed to get JWT token')



if not os.path.exists(DB_PATH):
    print("[+] Initializing stockDB.db...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    schema = """
    CREATE TABLE "exchange" (
        "id" INTEGER,
        "stock_exchange" TEXT,
        "mic" TEXT,
        "home_country" TEXT,
        PRIMARY KEY("id")
    );
    
    -- seed exchange data
    INSERT INTO "exchange" ("id", "stock_exchange", "mic", "home_country") VALUES (1, 'New York Stock Exchange', 'XNYS', 'USA');
    INSERT INTO "exchange" ("id", "stock_exchange", "mic", "home_country") VALUES (2, 'Nasdaq (US)', 'XNAS', 'USA');
    INSERT INTO "exchange" ("id", "stock_exchange", "mic", "home_country") VALUES (3, 'Shanghai Stock Exchange', 'XSHG', 'China');
    INSERT INTO "exchange" ("id", "stock_exchange", "mic", "home_country") VALUES (4, 'Euronext', 'XAMS', 'Netherlands');
    INSERT INTO "exchange" ("id", "stock_exchange", "mic", "home_country") VALUES (5, 'Euronext', 'XBRU', 'Belgium');
    INSERT INTO "exchange" ("id", "stock_exchange", "mic", "home_country") VALUES (6, 'Euronext', 'XMSM', 'Ireland');
    INSERT INTO "exchange" ("id", "stock_exchange", "mic", "home_country") VALUES (7, 'Euronext', 'XLIS', 'Portugal');
    INSERT INTO "exchange" ("id", "stock_exchange", "mic", "home_country") VALUES (8, 'Euronext', 'XOSL', 'Norway');
    INSERT INTO "exchange" ("id", "stock_exchange", "mic", "home_country") VALUES (9, 'Euronext', 'XPAR', 'France');
    INSERT INTO "exchange" ("id", "stock_exchange", "mic", "home_country") VALUES (10, 'Tokyo Stock Exchange', 'TYO', 'Japan');
    INSERT INTO "exchange" ("id", "stock_exchange", "mic", "home_country") VALUES (11, 'Japan Exchange Group', 'XJPX', 'Japan');
    INSERT INTO "exchange" ("id", "stock_exchange", "mic", "home_country") VALUES (12, 'Bombay Stock Exchange', 'XBOM', 'India');
    INSERT INTO "exchange" ("id", "stock_exchange", "mic", "home_country") VALUES (13, 'National Stock Exchange', 'XNSE', 'India');
    INSERT INTO "exchange" ("id", "stock_exchange", "mic", "home_country") VALUES (14, 'Shenzhen Stock Exchange', 'XSHE', 'China');
    INSERT INTO "exchange" ("id", "stock_exchange", "mic", "home_country") VALUES (15, 'Hong Kong Stock Exchange', 'XHKG', 'Hong Kong');
    INSERT INTO "exchange" ("id", "stock_exchange", "mic", "home_country") VALUES (16, 'Toronto Stock Exchange', 'XTSE', 'Canada');
    INSERT INTO "exchange" ("id", "stock_exchange", "mic", "home_country") VALUES (17, 'London Stock Exchange', 'XLON', 'United Kingdom');
    INSERT INTO "exchange" ("id", "stock_exchange", "mic", "home_country") VALUES (18, 'Saudi Stock Exchange', 'XSAU', 'Saudi Arabia');
    INSERT INTO "exchange" ("id", "stock_exchange", "mic", "home_country") VALUES (19, 'German Stock Exchange', 'XFRA', 'Germany');
    INSERT INTO "exchange" ("id", "stock_exchange", "mic", "home_country") VALUES (20, 'Copenhagen Stock Exchange', 'XCSE', 'Denmark');
    INSERT INTO "exchange" ("id", "stock_exchange", "mic", "home_country") VALUES (21, 'Stockhol Stock Exchange', 'XSTO', 'Sweden');
    INSERT INTO "exchange" ("id", "stock_exchange", "mic", "home_country") VALUES (22, 'Helsinki Stock Exchange', 'XHEL', 'Finland');
    INSERT INTO "exchange" ("id", "stock_exchange", "mic", "home_country") VALUES (23, 'Tallinn Stock Exchange', 'XTAL', 'Estonia');
    INSERT INTO "exchange" ("id", "stock_exchange", "mic", "home_country") VALUES (24, 'Riga Stock Exchange', 'XRIS', 'Latvia');
    INSERT INTO "exchange" ("id", "stock_exchange", "mic", "home_country") VALUES (25, 'Vilnius Stock Exchange', 'XLIT', 'Lithuania');
    INSERT INTO "exchange" ("id", "stock_exchange", "mic", "home_country") VALUES (26, 'Iceland Stock Exchange', 'XICE', 'Iceland');
    INSERT INTO "exchange" ("id", "stock_exchange", "mic", "home_country") VALUES (27, 'Taiwan Stock Exchange', 'XTAI', 'Taiwan');
    INSERT INTO "exchange" ("id", "stock_exchange", "mic", "home_country") VALUES (28, 'SIX Swiss Exchange', 'XSWX', 'Switzerland');
    INSERT INTO "exchange" ("id", "stock_exchange", "mic", "home_country") VALUES (29, 'Australian Securities Exchange', 'XASX', 'Australia');
    INSERT INTO "exchange" ("id", "stock_exchange", "mic", "home_country") VALUES (30, 'Korea Exchange', 'XKOS', 'South Korea');
    INSERT INTO "exchange" ("id", "stock_exchange", "mic", "home_country") VALUES (31, 'Johannesburg Stock Exchange', 'XJSE', 'South Africa');


    CREATE TABLE "Sectors" (
        "id" INTEGER,
        "sector" TEXT,
        "source" TEXT,
        PRIMARY KEY("id")
    );
    
     -- Seed Sectors data
    INSERT INTO "Sectors" ("id", "sector", "source") VALUES (1, 'Technology', 'yahoo');
    INSERT INTO "Sectors" ("id", "sector", "source") VALUES (2, 'Financial Services', 'yahoo');
    INSERT INTO "Sectors" ("id", "sector", "source") VALUES (3, 'Consumer Cyclical', 'yahoo');
    INSERT INTO "Sectors" ("id", "sector", "source") VALUES (4, 'Healthcare', 'yahoo');
    INSERT INTO "Sectors" ("id", "sector", "source") VALUES (5, 'Communication Services', 'yahoo');
    INSERT INTO "Sectors" ("id", "sector", "source") VALUES (6, 'Industrials', 'yahoo');
    INSERT INTO "Sectors" ("id", "sector", "source") VALUES (7, 'Consumer Defensive', 'yahoo');
    INSERT INTO "Sectors" ("id", "sector", "source") VALUES (8, 'Energy', 'yahoo');
    INSERT INTO "Sectors" ("id", "sector", "source") VALUES (9, 'Real Estate', 'yahoo');
    INSERT INTO "Sectors" ("id", "sector", "source") VALUES (10, 'Basic Materials', 'yahoo');
    INSERT INTO "Sectors" ("id", "sector", "source") VALUES (11, 'Utilities', 'yahoo');
    INSERT INTO "Sectors" ("id", "sector", "source") VALUES (12, 'Government Bonds', 'Custom');
    INSERT INTO "Sectors" ("id", "sector", "source") VALUES (13, 'Diversified', 'Custom');
    
    CREATE TABLE "industries" (
        "id" INTEGER,
        "name" TEXT,
        "yahooname" TEXT,
        "industrieID" INTEGER,
        PRIMARY KEY("id")
    );
    
        -- Seed industry data
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('1', 'Regulated Electric', 'Utilities - Regulated Electric', '11');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('2', 'Renewable', 'Utilities - Renewable', '11');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('3', 'Diversified', 'Utilities - Diversified', '11');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('4', 'Regulated Gas', 'Utilities - Regulated Gas', '11');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('5', 'Independent Power Producers', 'Utilities - Independent Power Producers', '11');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('6', 'Regulated Water', 'Utilities - Regulated Water', '11');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('7', 'Semiconductors', 'Semiconductors', '1');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('8', 'Software - Infrastructure', 'Software - Infrastructure', '1');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('9', 'Consumer Electronics', 'Consumer Electronics', '1');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('10', 'Software - Application', 'Software - Application', '1');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('11', 'Information Technology Services', 'Information Technology Services', '1');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('12', 'Communication Equipment', 'Communication Equipment', '1');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('13', 'Semiconductor Equipment & Materials', 'Semiconductor Equipment & Materials', '1');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('14', 'Computer Hardware', 'Computer Hardware', '1');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('15', 'Electronic Components', 'Electronic Components', '1');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('16', 'Scientific & Technical Instruments', 'Scientific & Technical Instruments', '1');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('17', 'Solar', 'Solar', '1');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('18', 'Electronics & Computer Distribution', 'Electronics & Computer Distribution', '1');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('19', 'Diversified', 'Banks - Diversified', '2');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('20', 'Credit Services', 'Credit Services', '2');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('21', 'Asset Management', 'Asset Management', '2');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('22', 'Diversified', 'Insurance - Diversified', '2');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('23', 'Regional', 'Banks - Regional', '2');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('24', 'Capital Markets', 'Capital Markets', '2');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('25', 'Financial Data & Stock Exchanges', 'Financial Data & Stock Exchanges', '2');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('26', 'Property & Casualty', 'Insurance - Property & Casualty', '2');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('27', 'Insurance Brokers', 'Insurance Brokers', '2');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('28', 'Life', 'Insurance - Life', '2');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('29', 'Specialty', 'Insurance - Specialty', '2');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('30', 'Mortgage Finance', 'Mortgage Finance', '2');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('31', 'Reinsurance', 'Insurance - Reinsurance', '2');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('32', 'Shell Companies', 'Shell Companies', '2');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('33', 'Financial Conglomerates', 'Financial Conglomerates', '2');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('34', 'Internet Retail', 'Internet Retail', '3');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('35', 'Auto Manufacturers', 'Auto Manufacturers', '3');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('36', 'Restaurants', 'Restaurants', '3');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('37', 'Home Improvement Retail', 'Home Improvement Retail', '3');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('38', 'Travel Services', 'Travel Services', '3');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('39', 'Specialty Retail', 'Specialty Retail', '3');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('40', 'Apparel Retail', 'Apparel Retail', '3');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('41', 'Residential Construction', 'Residential Construction', '3');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('42', 'Footwear & Accessories', 'Footwear & Accessories', '3');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('43', 'Packaging & Containers', 'Packaging & Containers', '3');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('44', 'Lodging', 'Lodging', '3');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('45', 'Auto Parts', 'Auto Parts', '3');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('46', 'Auto & Truck Dealerships', 'Auto & Truck Dealerships', '3');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('47', 'Resorts & Casinos', 'Resorts & Casinos', '3');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('48', 'Gambling', 'Gambling', '3');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('49', 'Leisure', 'Leisure', '3');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('50', 'Apparel Manufacturing', 'Apparel Manufacturing', '3');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('51', 'Furnishings, Fixtures & Appliances', 'Furnishings, Fixtures & Appliances', '3');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('52', 'Personal Services', 'Personal Services', '3');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('53', 'Recreational Vehicles', 'Recreational Vehicles', '3');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('54', 'Luxury Goods', 'Luxury Goods', '3');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('55', 'Department Stores', 'Department Stores', '3');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('56', 'Textile Manufacturing', 'Textile Manufacturing', '3');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('57', 'Drug Manufacturers - General', 'Drug Manufacturers - General', '4');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('58', 'Healthcare Plans', 'Healthcare Plans', '4');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('59', 'Medical Devices', 'Medical Devices', '4');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('60', 'Biotechnology', 'Biotechnology', '4');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('61', 'Diagnostics & Research', 'Diagnostics & Research', '4');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('62', 'Medical Instruments & Supplies', 'Medical Instruments & Supplies', '4');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('63', 'Medical Care Facilities', 'Medical Care Facilities', '4');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('64', 'Drug Manufacturers - Specialty & Generic', 'Drug Manufacturers - Specialty & Generic', '4');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('65', 'Medical Distribution', 'Medical Distribution', '4');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('66', 'Health Information Services', 'Health Information Services', '4');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('67', 'Pharmaceutical Retailers', 'Pharmaceutical Retailers', '4');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('68', 'Internet Content & Information', 'Internet Content & Information', '5');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('69', 'Telecom Services', 'Telecom Services', '5');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('70', 'Entertainment', 'Entertainment', '5');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('71', 'Electronic Gaming & Multimedia', 'Electronic Gaming & Multimedia', '5');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('72', 'Advertising Agencies', 'Advertising Agencies', '5');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('73', 'Publishing', 'Publishing', '5');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('74', 'Broadcasting', 'Broadcasting', '5');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('75', 'Aerospace & Defense', 'Aerospace & Defense', '6');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('76', 'Specialty Industrial Machinery', 'Specialty Industrial Machinery', '6');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('77', 'Railroads', 'Railroads', '6');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('78', 'Farm & Heavy Construction Machinery', 'Farm & Heavy Construction Machinery', '6');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('79', 'Building Products & Equipment', 'Building Products & Equipment', '6');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('80', 'Specialty Business Services', 'Specialty Business Services', '6');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('81', 'Integrated Freight & Logistics', 'Integrated Freight & Logistics', '6');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('82', 'Conglomerates', 'Conglomerates', '6');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('83', 'Engineering & Construction', 'Engineering & Construction', '6');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('84', 'Waste Management', 'Waste Management', '6');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('85', 'Industrial Distribution', 'Industrial Distribution', '6');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('86', 'Rental & Leasing Services', 'Rental & Leasing Services', '6');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('87', 'Electrical Equipment & Parts', 'Electrical Equipment & Parts', '6');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('88', 'Airlines', 'Airlines', '6');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('89', 'Trucking', 'Trucking', '6');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('90', 'Consulting Services', 'Consulting Services', '6');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('91', 'Tools & Accessories', 'Tools & Accessories', '6');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('92', 'Pollution & Treatment Controls', 'Pollution & Treatment Controls', '6');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('93', 'Security & Protection Services', 'Security & Protection Services', '6');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('94', 'Metal Fabrication', 'Metal Fabrication', '6');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('95', 'Marine Shipping', 'Marine Shipping', '6');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('96', 'Infrastructure Operations', 'Infrastructure Operations', '6');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('97', 'Staffing & Employment Services', 'Staffing & Employment Services', '6');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('98', 'Airports & Air Services', 'Airports & Air Services', '6');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('99', 'Business Equipment & Supplies', 'Business Equipment & Supplies', '6');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('100', 'Discount Stores', 'Discount Stores', '7');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('101', 'Household & Personal Products', 'Household & Personal Products', '7');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('102', 'Beverages - Non-Alcoholic', 'Beverages - Non-Alcoholic', '7');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('103', 'Tobacco', 'Tobacco', '7');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('104', 'Packaged Foods', 'Packaged Foods', '7');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('105', 'Confectioners', 'Confectioners', '7');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('106', 'Food Distribution', 'Food Distribution', '7');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('107', 'Grocery Stores', 'Grocery Stores', '7');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('108', 'Farm Products', 'Farm Products', '7');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('109', 'Beverages - Brewers', 'Beverages - Brewers', '7');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('110', 'Education & Training Services', 'Education & Training Services', '7');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('111', 'Beverages - Wineries & Distilleries', 'Beverages - Wineries & Distilleries', '7');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('112', 'Oil & Gas Integrated', 'Oil & Gas Integrated', '8');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('113', 'Oil & Gas Midstream', 'Oil & Gas Midstream', '8');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('114', 'Oil & Gas E&P', 'Oil & Gas E&P', '8');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('115', 'Oil & Gas Equipment & Services', 'Oil & Gas Equipment & Services', '8');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('116', 'Oil & Gas Refining & Marketing', 'Oil & Gas Refining & Marketing', '8');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('117', 'Uranium', 'Uranium', '8');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('118', 'Oil & Gas Drilling', 'Oil & Gas Drilling', '8');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('119', 'Thermal Coal', 'Thermal Coal', '8');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('120', 'REIT - Specialty', 'REIT - Specialty', '9');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('121', 'REIT - Industrial', 'REIT - Industrial', '9');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('122', 'REIT - Retail', 'REIT - Retail', '9');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('123', 'REIT - Residential', 'REIT - Residential', '9');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('124', 'REIT - Healthcare Facilities', 'REIT - Healthcare Facilities', '9');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('125', 'Real Estate Services', 'Real Estate Services', '9');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('126', 'REIT - Office', 'REIT - Office', '9');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('127', 'REIT - Diversified', 'REIT - Diversified', '9');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('128', 'REIT - Mortgage', 'REIT - Mortgage', '9');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('129', 'REIT - Hotel & Motel', 'REIT - Hotel & Motel', '9');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('130', 'Real Estate - Development', 'Real Estate - Development', '9');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('131', 'Real Estate - Diversified', 'Real Estate - Diversified', '9');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('132', 'Specialty Chemicals', 'Specialty Chemicals', '10');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('133', 'Gold', 'Gold', '10');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('134', 'Building Materials', 'Building Materials', '10');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('135', 'Copper', 'Copper', '10');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('136', 'Steel', 'Steel', '10');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('137', 'Agricultural Inputs', 'Agricultural Inputs', '10');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('138', 'Chemicals', 'Chemicals', '10');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('139', 'Other Industrial Metals & Mining', 'Other Industrial Metals & Mining', '10');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('140', 'Lumber & Wood Production', 'Lumber & Wood Production', '10');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('141', 'Aluminum', 'Aluminum', '10');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('142', 'Other Precious Metals & Mining', 'Other Precious Metals & Mining', '10');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('143', 'Coking Coal', 'Coking Coal', '10');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('144', 'Paper & Paper Products', 'Paper & Paper Products', '10');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('145', 'Silver', 'Silver', '10');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('146', 'Government Bond', 'NL Staatsobligatie', '12');
    INSERT INTO "industries" ("id", "name", "yahooname", "industrieID") VALUES ('147', 'All', 'All', '13');
    
    CREATE TABLE "portfolioTransactions" (
        "id" INTEGER,
        "tickerid" INTEGER,
        "date" INTEGER,
        "quantity" INTEGER,
        "currency" INTEGER,
        "stockPrice" INTEGER,
        "Type" TEXT,
        "transactionFee" INTEGER,
        PRIMARY KEY("id" AUTOINCREMENT),
        FOREIGN KEY("tickerid") REFERENCES "Stocks"("id")
    );
    CREATE TABLE "industryBenchmark" (
        "id" INTEGER,
        "industryID" INTEGER UNIQUE,
        "price" REAL,
        "beta" REAL,
        "peratio" REAL,
        "pbratio" REAL,
        "icr" REAL,
        "currentRatio" REAL,
        "dividentYield" REAL,
        "percRandD" REAL,
        "lastReturn" REAL,
        "fiveYearAverageReturn" REAL,
        "percentageMakingProfitLastFiveYears" REAL,
        PRIMARY KEY("id" AUTOINCREMENT),
        FOREIGN KEY("industryID") REFERENCES "industries"("id")
    );
    CREATE TABLE "profiles" (
        "id" INTEGER,
        "type" TEXT,
        PRIMARY KEY("id" AUTOINCREMENT)
    );
    
    -- seed profile data
    INSERT INTO "profiles" ("id", "type") VALUES (1, 'Defensive profile');
    
    CREATE TABLE "profileMetrics" (
        "id" INTEGER,
        "profile_id" INTEGER,
        "minValue" INTEGER,
        "maxValue" INTEGER,
        "direction" TEXT,
        "redFlag" INTEGER,
        "metric" TEXT,
        PRIMARY KEY("id" AUTOINCREMENT),
        FOREIGN KEY("profile_id") REFERENCES "profiles"("id")
    );
    
    -- seed base profile
    INSERT INTO "profileMetrics" ("id", "profile_id", "minValue", "maxValue", "direction", "redFlag", "metric") VALUES (9, 1, 0.99, 1.05, 'D', NULL, 'beta');
    INSERT INTO "profileMetrics" ("id", "profile_id", "minValue", "maxValue", "direction", "redFlag", "metric") VALUES (10, 1, 10, 20, 'D', NULL, 'peRatio');
    INSERT INTO "profileMetrics" ("id", "profile_id", "minValue", "maxValue", "direction", "redFlag", "metric") VALUES (11, 1, 2, 5, 'D', NULL, 'pbRatio');
    INSERT INTO "profileMetrics" ("id", "profile_id", "minValue", "maxValue", "direction", "redFlag", "metric") VALUES (12, 1, 5, 7, 'U', NULL, 'icr');
    INSERT INTO "profileMetrics" ("id", "profile_id", "minValue", "maxValue", "direction", "redFlag", "metric") VALUES (13, 1, 0.95, 1.05, 'U', NULL, 'currentRatio');
    INSERT INTO "profileMetrics" ("id", "profile_id", "minValue", "maxValue", "direction", "redFlag", "metric") VALUES (14, 1, 3, 5, 'U', 10, 'dividendYield');
    INSERT INTO "profileMetrics" ("id", "profile_id", "minValue", "maxValue", "direction", "redFlag", "metric") VALUES (15, 1, 1, 5, 'U', 25, 'percRandD');
    INSERT INTO "profileMetrics" ("id", "profile_id", "minValue", "maxValue", "direction", "redFlag", "metric") VALUES (16, 1, 80, 99, 'U', NULL, 'percentageMakingProfitLastFiveYears');

    
    CREATE TABLE "Stocks" (
        "id" INTEGER,
        "ticker" TEXT,
        "stockname" TEXT,
        "Exchange" TEXT,
        "DateAdded" TEXT,
        "Status" TEXT,
        "industryID" INTEGER,
        "sectorID" INTEGER,
        "isWatchlist" INTEGER,
        "strategicEvaluation" TEXT,
        "type" TEXT,
        "assetType" TEXT,
        PRIMARY KEY("id"),
        FOREIGN KEY("industryID") REFERENCES "industries"("id"),
        FOREIGN KEY("sectorID") REFERENCES "Sectors"("id")
    );
    CREATE TABLE "stockhistory" (
        "id" INTEGER UNIQUE,
        "stockID" INTEGER NOT NULL,
        "date" TEXT NOT NULL,
        "price" INTEGER,
        "operatingIncom" INTEGER,
        "icr" INTEGER,
        "currentRatio" INTEGER,
        "pbratio" INTEGER,
        "peratio" INTEGER,
        "beta" INTEGER,
        "lastReturn" INTEGER,
        "fiveYearAverageReturn" NUMERIC,
        "dividentYield" INTEGER,
        "RandDExpense" INTEGER,
        "currency" INTEGER,
        "revenue" INTEGER,
        "percentageMakingProfitLastFiveYears" INTEGER,
        "debt" INTEGER,
        PRIMARY KEY("id" AUTOINCREMENT),
        FOREIGN KEY("stockID") REFERENCES "Stocks"("id")
    );
    
    CREATE INDEX idx_stockhistory_date ON stockhistory(date);
    CREATE INDEX idx_stockhistory_stockID ON stockhistory(stockID);
    CREATE INDEX idx_stockhistory_stockID_date ON stockhistory(stockID, date);
    
    CREATE TABLE "dividends" (
        "id" INTEGER,
        "stockID" INTEGER,
        "date" INTEGER,
        "dividendPerShare" INTEGER,
        "yahooDate" INTEGER,
        PRIMARY KEY("id" AUTOINCREMENT),
        FOREIGN KEY("stockID") REFERENCES "Stocks"("id")
    );
    CREATE TABLE "dividendExpectations" (
        "id" INTEGER,
        "stockID" INTEGER NOT NULL,
        "expectedMonth" TEXT NOT NULL,
        "expectedDividendPerShare" REAL NOT NULL,
        "expectedDay" INTEGER,
        PRIMARY KEY("id" AUTOINCREMENT),
        FOREIGN KEY("stockID") REFERENCES "Stocks"("id")
    );
    CREATE TABLE "expenseType" (
        "id" INTEGER NOT NULL UNIQUE,
        "expenseType" TEXT,
        PRIMARY KEY("id" AUTOINCREMENT)
    );
    
    -- seed basic expense types
    INSERT INTO "expenseType" ("id", "expenseType") VALUES (1, 'Savings');
    INSERT INTO "expenseType" ("id", "expenseType") VALUES (2, 'Investments');
    INSERT INTO "expenseType" ("id", "expenseType") VALUES (3, 'Debt interest payments');
    INSERT INTO "expenseType" ("id", "expenseType") VALUES (4, 'Housing');
    INSERT INTO "expenseType" ("id", "expenseType") VALUES (5, 'Groceries');
    INSERT INTO "expenseType" ("id", "expenseType") VALUES (6, 'Sport');
    INSERT INTO "expenseType" ("id", "expenseType") VALUES (7, 'Subscriptions');
    INSERT INTO "expenseType" ("id", "expenseType") VALUES (8, 'Insurance');
    INSERT INTO "expenseType" ("id", "expenseType") VALUES (9, 'Dining Out');
    INSERT INTO "expenseType" ("id", "expenseType") VALUES (10, 'Personal Care');
    INSERT INTO "expenseType" ("id", "expenseType") VALUES (11, 'Entertainment');
    INSERT INTO "expenseType" ("id", "expenseType") VALUES (12, 'Utilities');
    INSERT INTO "expenseType" ("id", "expenseType") VALUES (13, 'Taxes');
    INSERT INTO "expenseType" ("id", "expenseType") VALUES (15, 'Miscellaneous or unknown');
    INSERT INTO "expenseType" ("id", "expenseType") VALUES (16, 'Banking');
    INSERT INTO "expenseType" ("id", "expenseType") VALUES (17, 'Club memberships');
    INSERT INTO "expenseType" ("id", "expenseType") VALUES (18, 'Charities');
    INSERT INTO "expenseType" ("id", "expenseType") VALUES (19, 'Gifts');


    
    CREATE TABLE "personalFinance" (
        "id" INTEGER NOT NULL UNIQUE,
        "salary" INTEGER,
        "date" TEXT,
        "savings" INTEGER,
        PRIMARY KEY("id" AUTOINCREMENT)
    );
    
    INSERT INTO "personalFinance" ("id", "salary", "date", "savings") VALUES (1, 0, '2025-01-01', 0);


    CREATE TABLE "expenses" (
        "id" INTEGER NOT NULL UNIQUE,
        "expense" TEXT,
        "type" INTEGER,
        "frequency" INTEGER,
        "cost" INTEGER,
        "survival" INTEGER,
        PRIMARY KEY("id" AUTOINCREMENT),
        FOREIGN KEY("type") REFERENCES "expenseType"("id")
    );
    CREATE TABLE "economyhistory" (
        "id" INTEGER,
        "date" TEXT,
        "inflation" INTEGER,
        "ECBInterest" INTEGER,
        "NL_Unemployment" INTEGER,
        "NL_ConsumerConfidence" INTEGER,
        "EUR_USD_ExchangeRate" INTEGER,
        "NL_RetailSales" INTEGER,
        "NL_GDPGrowth" INTEGER,
        "NL_IndustrialProduction" INTEGER,
        "NL_Bankrupcies" INTEGER,
        "EU_CLI" INTEGER,
        PRIMARY KEY("id")
    );
    """

    try:
        cursor.executescript(schema)
        print("[✓] Schema and seed data executed successfully.")
    except sqlite3.Error as e:
        print(f"[!] SQLite error: {e}")


    conn.commit()
    conn.close()
    print("[X] Database created.")
    print("[x] Starting data interaction layer")
    subprocess.Popen(["python3", "dataApp.py"])
    wait_for_port("127.0.0.1", 5001)
    sleep(5)
    print("[.] Pulling initial data from yahoo finance, this can take a while (up to 3 hours).")
    APIAccessToken = get_jwt_token()
    print("[X] got a data access token")
    
    # Lets fetch the initial economic data
    try:
        headers = {'Authorization': f'Bearer {APIAccessToken}'}
        economyURL = Config.dataURL + "/updateEconomics"
        response = requests.get(economyURL, headers=headers)
        sleep(10)
        print("[x] pulled CBS, ECB and OECD data")
        
    except requests.RequestException as e:
        print(jsonify({'error': str(e)}), 500)
    print("[x] Start to import initial stock set, this can take up to 15 minutes")
    try:
        headers = {'Authorization': f'Bearer {APIAccessToken}'}
        refreshTickerURL = Config.dataURL + "/refresh-ticker-data"
        for exchange in Config.exchanges:
            response = requests.post(refreshTickerURL, json={'exchange': exchange}, headers=headers)
            print("[x] Imported initial stock set for: ", exchange)
        print("[x] completed loading exchange tickets")
    except requests.RequestException as e:
        print(jsonify({'error': str(e)}), 500)
    sleep(15)
    try:
        startURL = Config.dataURL + "/start-update"
        headers = {'Authorization': f'Bearer {APIAccessToken}'}
        response = requests.post(startURL, headers=headers)
        if response.status_code == 202:
            print("[x] started loading stocks, process will coninue in the background, it can take up to 3 hours to complete installation, please sit-back and enjoy")
    except requests.RequestException as e:
        print("Error: ", e
    
else:
    print("[!] stockDB.sqlite already exists. Skipping initialization.")

 