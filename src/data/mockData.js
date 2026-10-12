/**
 * City gazetteer used for map centering and autocomplete.
 *
 * This is the only mock data kept after Batch 1. It is scheduled for deletion
 * in Batch 9 once locations come from the backend. It covers major US cities
 * plus the Canadian cities relevant to the carrier's terminals and lanes.
 */
export const US_CITIES = [
  // Alabama
  { label: 'Birmingham, AL',      lat: 33.5186,  lng: -86.8104  },
  { label: 'Montgomery, AL',      lat: 32.3792,  lng: -86.3077  },
  { label: 'Huntsville, AL',      lat: 34.7304,  lng: -86.5861  },
  { label: 'Mobile, AL',          lat: 30.6954,  lng: -88.0399  },
  // Alaska
  { label: 'Anchorage, AK',       lat: 61.2181,  lng: -149.9003 },
  { label: 'Fairbanks, AK',       lat: 64.8378,  lng: -147.7164 },
  // Arizona
  { label: 'Phoenix, AZ',         lat: 33.4484,  lng: -112.0740 },
  { label: 'Tucson, AZ',          lat: 32.2226,  lng: -110.9747 },
  { label: 'Mesa, AZ',            lat: 33.4152,  lng: -111.8315 },
  { label: 'Chandler, AZ',        lat: 33.3062,  lng: -111.8413 },
  { label: 'Scottsdale, AZ',      lat: 33.4942,  lng: -111.9261 },
  { label: 'Flagstaff, AZ',       lat: 35.1983,  lng: -111.6513 },
  { label: 'Tempe, AZ',           lat: 33.4255,  lng: -111.9400 },
  // Arkansas
  { label: 'Little Rock, AR',     lat: 34.7465,  lng: -92.2896  },
  { label: 'Fort Smith, AR',      lat: 35.3859,  lng: -94.3985  },
  { label: 'Fayetteville, AR',    lat: 36.0626,  lng: -94.1574  },
  // California
  { label: 'Los Angeles, CA',     lat: 34.0522,  lng: -118.2437 },
  { label: 'San Diego, CA',       lat: 32.7157,  lng: -117.1611 },
  { label: 'San Francisco, CA',   lat: 37.7749,  lng: -122.4194 },
  { label: 'San Jose, CA',        lat: 37.3382,  lng: -121.8863 },
  { label: 'Sacramento, CA',      lat: 38.5816,  lng: -121.4944 },
  { label: 'Fresno, CA',          lat: 36.7378,  lng: -119.7871 },
  { label: 'Oakland, CA',         lat: 37.8044,  lng: -122.2711 },
  { label: 'Long Beach, CA',      lat: 33.7701,  lng: -118.1937 },
  { label: 'Bakersfield, CA',     lat: 35.3733,  lng: -119.0187 },
  { label: 'Riverside, CA',       lat: 33.9533,  lng: -117.3961 },
  { label: 'Stockton, CA',        lat: 37.9577,  lng: -121.2908 },
  // Colorado
  { label: 'Denver, CO',          lat: 39.7392,  lng: -104.9903 },
  { label: 'Colorado Springs, CO',lat: 38.8339,  lng: -104.8214 },
  { label: 'Aurora, CO',          lat: 39.7294,  lng: -104.8319 },
  { label: 'Fort Collins, CO',    lat: 40.5853,  lng: -105.0844 },
  { label: 'Boulder, CO',         lat: 40.0150,  lng: -105.2705 },
  { label: 'Pueblo, CO',          lat: 38.2544,  lng: -104.6091 },
  // Connecticut
  { label: 'Bridgeport, CT',      lat: 41.1865,  lng: -73.1952  },
  { label: 'Hartford, CT',        lat: 41.7658,  lng: -72.6734  },
  { label: 'New Haven, CT',       lat: 41.3083,  lng: -72.9279  },
  { label: 'Stamford, CT',        lat: 41.0534,  lng: -73.5387  },
  // Delaware
  { label: 'Wilmington, DE',      lat: 39.7447,  lng: -75.5484  },
  { label: 'Dover, DE',           lat: 39.1582,  lng: -75.5244  },
  // Florida
  { label: 'Jacksonville, FL',    lat: 30.3322,  lng: -81.6557  },
  { label: 'Miami, FL',           lat: 25.7617,  lng: -80.1918  },
  { label: 'Tampa, FL',           lat: 27.9506,  lng: -82.4572  },
  { label: 'Orlando, FL',         lat: 28.5383,  lng: -81.3792  },
  { label: 'St. Petersburg, FL',  lat: 27.7676,  lng: -82.6403  },
  { label: 'Fort Lauderdale, FL', lat: 26.1224,  lng: -80.1373  },
  { label: 'Tallahassee, FL',     lat: 30.4518,  lng: -84.2807  },
  { label: 'Gainesville, FL',     lat: 29.6516,  lng: -82.3248  },
  // Georgia
  { label: 'Atlanta, GA',         lat: 33.7490,  lng: -84.3880  },
  { label: 'Columbus, GA',        lat: 32.4610,  lng: -84.9877  },
  { label: 'Augusta, GA',         lat: 33.4735,  lng: -82.0105  },
  { label: 'Savannah, GA',        lat: 32.0835,  lng: -81.0998  },
  { label: 'Macon, GA',           lat: 32.8407,  lng: -83.6324  },
  // Hawaii
  { label: 'Honolulu, HI',        lat: 21.3069,  lng: -157.8583 },
  { label: 'Hilo, HI',            lat: 19.7070,  lng: -155.0885 },
  // Idaho
  { label: 'Boise, ID',           lat: 43.6150,  lng: -116.2023 },
  { label: 'Meridian, ID',        lat: 43.6121,  lng: -116.3915 },
  { label: 'Nampa, ID',           lat: 43.5407,  lng: -116.5635 },
  { label: 'Idaho Falls, ID',     lat: 43.4927,  lng: -112.0408 },
  // Illinois
  { label: 'Chicago, IL',         lat: 41.8781,  lng: -87.6298  },
  { label: 'Aurora, IL',          lat: 41.7606,  lng: -88.3201  },
  { label: 'Rockford, IL',        lat: 42.2711,  lng: -89.0937  },
  { label: 'Joliet, IL',          lat: 41.5250,  lng: -88.0817  },
  { label: 'Springfield, IL',     lat: 39.7817,  lng: -89.6501  },
  { label: 'Peoria, IL',          lat: 40.6936,  lng: -89.5890  },
  // Indiana
  { label: 'Indianapolis, IN',    lat: 39.7684,  lng: -86.1581  },
  { label: 'Fort Wayne, IN',      lat: 41.0793,  lng: -85.1394  },
  { label: 'Evansville, IN',      lat: 37.9716,  lng: -87.5711  },
  { label: 'South Bend, IN',      lat: 41.6764,  lng: -86.2520  },
  // Iowa
  { label: 'Des Moines, IA',      lat: 41.5868,  lng: -93.6250  },
  { label: 'Cedar Rapids, IA',    lat: 41.9779,  lng: -91.6656  },
  { label: 'Davenport, IA',       lat: 41.5236,  lng: -90.5776  },
  { label: 'Iowa City, IA',       lat: 41.6611,  lng: -91.5302  },
  // Kansas
  { label: 'Wichita, KS',         lat: 37.6872,  lng: -97.3301  },
  { label: 'Overland Park, KS',   lat: 38.9822,  lng: -94.6708  },
  { label: 'Kansas City, KS',     lat: 39.1141,  lng: -94.6275  },
  { label: 'Topeka, KS',          lat: 39.0473,  lng: -95.6752  },
  // Kentucky
  { label: 'Louisville, KY',      lat: 38.2527,  lng: -85.7585  },
  { label: 'Lexington, KY',       lat: 38.0406,  lng: -84.5037  },
  { label: 'Bowling Green, KY',   lat: 36.9903,  lng: -86.4436  },
  // Louisiana
  { label: 'New Orleans, LA',     lat: 29.9511,  lng: -90.0715  },
  { label: 'Baton Rouge, LA',     lat: 30.4515,  lng: -91.1871  },
  { label: 'Shreveport, LA',      lat: 32.5252,  lng: -93.7502  },
  { label: 'Lafayette, LA',       lat: 30.2241,  lng: -92.0198  },
  // Maine
  { label: 'Portland, ME',        lat: 43.6591,  lng: -70.2568  },
  { label: 'Bangor, ME',          lat: 44.8012,  lng: -68.7778  },
  // Maryland
  { label: 'Baltimore, MD',       lat: 39.2904,  lng: -76.6122  },
  { label: 'Frederick, MD',       lat: 39.4143,  lng: -77.4105  },
  { label: 'Rockville, MD',       lat: 39.0840,  lng: -77.1528  },
  // Massachusetts
  { label: 'Boston, MA',          lat: 42.3601,  lng: -71.0589  },
  { label: 'Worcester, MA',       lat: 42.2626,  lng: -71.8023  },
  { label: 'Springfield, MA',     lat: 42.1015,  lng: -72.5898  },
  { label: 'Cambridge, MA',       lat: 42.3736,  lng: -71.1097  },
  { label: 'Lowell, MA',          lat: 42.6334,  lng: -71.3162  },
  // Michigan
  { label: 'Detroit, MI',         lat: 42.3314,  lng: -83.0458  },
  { label: 'Grand Rapids, MI',    lat: 42.9634,  lng: -85.6681  },
  { label: 'Warren, MI',          lat: 42.4775,  lng: -83.0277  },
  { label: 'Lansing, MI',         lat: 42.7325,  lng: -84.5555  },
  { label: 'Ann Arbor, MI',       lat: 42.2808,  lng: -83.7430  },
  { label: 'Flint, MI',           lat: 43.0125,  lng: -83.6875  },
  // Minnesota
  { label: 'Minneapolis, MN',     lat: 44.9778,  lng: -93.2650  },
  { label: 'Saint Paul, MN',      lat: 44.9537,  lng: -93.0900  },
  { label: 'Rochester, MN',       lat: 44.0121,  lng: -92.4802  },
  { label: 'Duluth, MN',          lat: 46.7867,  lng: -92.1005  },
  // Mississippi
  { label: 'Jackson, MS',         lat: 32.2988,  lng: -90.1848  },
  { label: 'Gulfport, MS',        lat: 30.3674,  lng: -89.0928  },
  { label: 'Hattiesburg, MS',     lat: 31.3271,  lng: -89.2903  },
  // Missouri
  { label: 'Kansas City, MO',     lat: 39.0997,  lng: -94.5786  },
  { label: 'St. Louis, MO',       lat: 38.6270,  lng: -90.1994  },
  { label: 'Springfield, MO',     lat: 37.2153,  lng: -93.2982  },
  { label: 'Columbia, MO',        lat: 38.9517,  lng: -92.3341  },
  // Montana
  { label: 'Billings, MT',        lat: 45.7833,  lng: -108.5007 },
  { label: 'Missoula, MT',        lat: 46.8721,  lng: -113.9940 },
  { label: 'Great Falls, MT',     lat: 47.4941,  lng: -111.2833 },
  // Nebraska
  { label: 'Omaha, NE',           lat: 41.2565,  lng: -95.9345  },
  { label: 'Lincoln, NE',         lat: 40.8136,  lng: -96.7026  },
  { label: 'Bellevue, NE',        lat: 41.1544,  lng: -95.9146  },
  // Nevada
  { label: 'Las Vegas, NV',       lat: 36.1699,  lng: -115.1398 },
  { label: 'Henderson, NV',       lat: 36.0397,  lng: -114.9817 },
  { label: 'Reno, NV',            lat: 39.5296,  lng: -119.8138 },
  { label: 'North Las Vegas, NV', lat: 36.1989,  lng: -115.1175 },
  // New Hampshire
  { label: 'Manchester, NH',      lat: 42.9956,  lng: -71.4548  },
  { label: 'Nashua, NH',          lat: 42.7654,  lng: -71.4676  },
  { label: 'Concord, NH',         lat: 43.2081,  lng: -71.5376  },
  // New Jersey
  { label: 'Newark, NJ',          lat: 40.7357,  lng: -74.1724  },
  { label: 'Jersey City, NJ',     lat: 40.7178,  lng: -74.0431  },
  { label: 'Paterson, NJ',        lat: 40.9168,  lng: -74.1719  },
  { label: 'Trenton, NJ',         lat: 40.2171,  lng: -74.7429  },
  // New Mexico
  { label: 'Albuquerque, NM',     lat: 35.0844,  lng: -106.6504 },
  { label: 'Las Cruces, NM',      lat: 32.3199,  lng: -106.7637 },
  { label: 'Rio Rancho, NM',      lat: 35.2328,  lng: -106.6630 },
  { label: 'Santa Fe, NM',        lat: 35.6869,  lng: -105.9378 },
  // New York
  { label: 'New York City, NY',   lat: 40.7128,  lng: -74.0060  },
  { label: 'Buffalo, NY',         lat: 42.8864,  lng: -78.8784  },
  { label: 'Rochester, NY',       lat: 43.1566,  lng: -77.6088  },
  { label: 'Yonkers, NY',         lat: 40.9312,  lng: -73.8988  },
  { label: 'Syracuse, NY',        lat: 43.0481,  lng: -76.1474  },
  { label: 'Albany, NY',          lat: 42.6526,  lng: -73.7562  },
  // North Carolina
  { label: 'Charlotte, NC',       lat: 35.2271,  lng: -80.8431  },
  { label: 'Raleigh, NC',         lat: 35.7796,  lng: -78.6382  },
  { label: 'Greensboro, NC',      lat: 36.0726,  lng: -79.7920  },
  { label: 'Durham, NC',          lat: 35.9940,  lng: -78.8986  },
  { label: 'Winston-Salem, NC',   lat: 36.0999,  lng: -80.2442  },
  { label: 'Fayetteville, NC',    lat: 35.0527,  lng: -78.8784  },
  // North Dakota
  { label: 'Fargo, ND',           lat: 46.8772,  lng: -96.7898  },
  { label: 'Bismarck, ND',        lat: 46.8083,  lng: -100.7837 },
  { label: 'Grand Forks, ND',     lat: 47.9253,  lng: -97.0329  },
  // Ohio
  { label: 'Columbus, OH',        lat: 39.9612,  lng: -82.9988  },
  { label: 'Cleveland, OH',       lat: 41.4993,  lng: -81.6944  },
  { label: 'Cincinnati, OH',      lat: 39.1031,  lng: -84.5120  },
  { label: 'Toledo, OH',          lat: 41.6639,  lng: -83.5552  },
  { label: 'Akron, OH',           lat: 41.0814,  lng: -81.5190  },
  { label: 'Dayton, OH',          lat: 39.7589,  lng: -84.1916  },
  // Oklahoma
  { label: 'Oklahoma City, OK',   lat: 35.4676,  lng: -97.5164  },
  { label: 'Tulsa, OK',           lat: 36.1540,  lng: -95.9928  },
  { label: 'Norman, OK',          lat: 35.2226,  lng: -97.4395  },
  // Oregon
  { label: 'Portland, OR',        lat: 45.5051,  lng: -122.6750 },
  { label: 'Salem, OR',           lat: 44.9429,  lng: -123.0351 },
  { label: 'Eugene, OR',          lat: 44.0521,  lng: -123.0868 },
  { label: 'Bend, OR',            lat: 44.0582,  lng: -121.3153 },
  // Pennsylvania
  { label: 'Philadelphia, PA',    lat: 39.9526,  lng: -75.1652  },
  { label: 'Pittsburgh, PA',      lat: 40.4406,  lng: -79.9959  },
  { label: 'Allentown, PA',       lat: 40.6084,  lng: -75.4902  },
  { label: 'Erie, PA',            lat: 42.1292,  lng: -80.0851  },
  { label: 'Reading, PA',         lat: 40.3356,  lng: -75.9269  },
  { label: 'Scranton, PA',        lat: 41.4090,  lng: -75.6624  },
  // Rhode Island
  { label: 'Providence, RI',      lat: 41.8240,  lng: -71.4128  },
  { label: 'Cranston, RI',        lat: 41.7798,  lng: -71.4373  },
  // South Carolina
  { label: 'Columbia, SC',        lat: 34.0007,  lng: -81.0348  },
  { label: 'Charleston, SC',      lat: 32.7765,  lng: -79.9311  },
  { label: 'Greenville, SC',      lat: 34.8526,  lng: -82.3940  },
  { label: 'Spartanburg, SC',     lat: 34.9496,  lng: -81.9321  },
  // South Dakota
  { label: 'Sioux Falls, SD',     lat: 43.5473,  lng: -96.7283  },
  { label: 'Rapid City, SD',      lat: 44.0805,  lng: -103.2310 },
  { label: 'Aberdeen, SD',        lat: 45.4647,  lng: -98.4865  },
  // Tennessee
  { label: 'Nashville, TN',       lat: 36.1627,  lng: -86.7816  },
  { label: 'Memphis, TN',         lat: 35.1495,  lng: -90.0490  },
  { label: 'Knoxville, TN',       lat: 35.9606,  lng: -83.9207  },
  { label: 'Chattanooga, TN',     lat: 35.0456,  lng: -85.3097  },
  { label: 'Clarksville, TN',     lat: 36.5298,  lng: -87.3595  },
  // Texas
  { label: 'Houston, TX',         lat: 29.7604,  lng: -95.3698  },
  { label: 'San Antonio, TX',     lat: 29.4241,  lng: -98.4936  },
  { label: 'Dallas, TX',          lat: 32.7767,  lng: -96.7970  },
  { label: 'Austin, TX',          lat: 30.2672,  lng: -97.7431  },
  { label: 'Fort Worth, TX',      lat: 32.7555,  lng: -97.3308  },
  { label: 'El Paso, TX',         lat: 31.7619,  lng: -106.4850 },
  { label: 'Arlington, TX',       lat: 32.7357,  lng: -97.1081  },
  { label: 'Corpus Christi, TX',  lat: 27.8006,  lng: -97.3964  },
  { label: 'Laredo, TX',          lat: 27.5036,  lng: -99.5075  },
  { label: 'Lubbock, TX',         lat: 33.5779,  lng: -101.8552 },
  { label: 'Amarillo, TX',        lat: 35.2220,  lng: -101.8313 },
  { label: 'Waco, TX',            lat: 31.5493,  lng: -97.1467  },
  { label: 'Plano, TX',           lat: 33.0198,  lng: -96.6989  },
  // Utah
  { label: 'Salt Lake City, UT',  lat: 40.7608,  lng: -111.8910 },
  { label: 'West Valley City, UT',lat: 40.6916,  lng: -112.0010 },
  { label: 'Provo, UT',           lat: 40.2338,  lng: -111.6585 },
  { label: 'Ogden, UT',           lat: 41.2230,  lng: -111.9738 },
  // Vermont
  { label: 'Burlington, VT',      lat: 44.4759,  lng: -73.2121  },
  { label: 'Rutland, VT',         lat: 43.6106,  lng: -72.9726  },
  // Virginia
  { label: 'Virginia Beach, VA',  lat: 36.8529,  lng: -75.9780  },
  { label: 'Norfolk, VA',         lat: 36.8508,  lng: -76.2859  },
  { label: 'Chesapeake, VA',      lat: 36.7682,  lng: -76.2875  },
  { label: 'Richmond, VA',        lat: 37.5407,  lng: -77.4360  },
  { label: 'Newport News, VA',    lat: 37.0871,  lng: -76.4730  },
  { label: 'Alexandria, VA',      lat: 38.8048,  lng: -77.0469  },
  { label: 'Roanoke, VA',         lat: 37.2710,  lng: -79.9414  },
  // Washington
  { label: 'Seattle, WA',         lat: 47.6062,  lng: -122.3321 },
  { label: 'Spokane, WA',         lat: 47.6588,  lng: -117.4260 },
  { label: 'Tacoma, WA',          lat: 47.2529,  lng: -122.4443 },
  { label: 'Vancouver, WA',       lat: 45.6387,  lng: -122.6615 },
  { label: 'Bellevue, WA',        lat: 47.6101,  lng: -122.2015 },
  { label: 'Kennewick, WA',       lat: 46.2112,  lng: -119.1372 },
  // West Virginia
  { label: 'Charleston, WV',      lat: 38.3498,  lng: -81.6326  },
  { label: 'Huntington, WV',      lat: 38.4192,  lng: -82.4452  },
  { label: 'Morgantown, WV',      lat: 39.6295,  lng: -79.9559  },
  // Wisconsin
  { label: 'Milwaukee, WI',       lat: 43.0389,  lng: -87.9065  },
  { label: 'Madison, WI',         lat: 43.0731,  lng: -89.4012  },
  { label: 'Green Bay, WI',       lat: 44.5133,  lng: -88.0133  },
  { label: 'Kenosha, WI',         lat: 42.5847,  lng: -87.8212  },
  // Wyoming
  { label: 'Cheyenne, WY',        lat: 41.1400,  lng: -104.8202 },
  { label: 'Casper, WY',          lat: 42.8666,  lng: -106.3131 },
  { label: 'Laramie, WY',         lat: 41.3114,  lng: -105.5911 },

  // ── Canada ──────────────────────────────────────────────
  // Ontario
  { label: 'Toronto, ON',         lat: 43.6532,  lng: -79.3832  },
  { label: 'Mississauga, ON',     lat: 43.5890,  lng: -79.6441  },
  { label: 'Ottawa, ON',          lat: 45.4215,  lng: -75.6972  },
  { label: 'Hamilton, ON',        lat: 43.2557,  lng: -79.8711  },
  { label: 'London, ON',          lat: 42.9849,  lng: -81.2453  },
  { label: 'Windsor, ON',         lat: 42.3149,  lng: -83.0364  },
  // Quebec
  { label: 'Montreal, QC',        lat: 45.5019,  lng: -73.5674  },
  { label: 'Quebec City, QC',     lat: 46.8139,  lng: -71.2080  },
  // Manitoba
  { label: 'Winnipeg, MB',        lat: 49.8951,  lng: -97.1384  },
  // Saskatchewan
  { label: 'Regina, SK',          lat: 50.4452,  lng: -104.6189 },
  // Alberta
  { label: 'Calgary, AB',         lat: 51.0447,  lng: -114.0719 },
  { label: 'Edmonton, AB',        lat: 53.5461,  lng: -113.4938 },
  // British Columbia
  { label: 'Vancouver, BC',       lat: 49.2827,  lng: -123.1207 },
  // Nova Scotia
  { label: 'Halifax, NS',         lat: 44.6488,  lng: -63.5752  },
  // New Brunswick
  { label: 'Moncton, NB',         lat: 46.0878,  lng: -64.7782  },
];
