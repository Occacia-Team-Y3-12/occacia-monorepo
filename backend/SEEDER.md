# Occacia Seeder Guide

## How to run
From `backend/`:

```bash
python -m app.scripts.seed
```

## Seeded credentials

### Admins
- `boss@occacia.com` / `SuperSecretPassword123!`
- `kashmikat@gmail.com` / `SuperSecretPassword123!`

### Customer
- `customer.test@occacia.com` / `testpass1`

### Vendors
- Default vendor password: `Vendor123!`
- Photography vendor password: `Abc@123` (for `tisal.20221672@iit.ac.lk`)

All vendors are approved (`approval_status=APPROVED`, `is_verified=true`, `approved_at` set).  
All organizations are approved (`status=approved`, `reviewed_at` set, `reviewed_by` admin id).

## Seeded vendor inventory

### Cakes & Bakery
| Vendor | Vendor Email | Offering | Price (LKR) | Unit | Quality |
| --- | --- | --- | --- | --- | --- |
| Cakes by Caramel | orders@cakesbycaramel.lk | Custom Celebration Cake | 42,000 | cake | HIGH |
| Kandy Sweet Oven | orders@kandysweetoven.lk | Buttercream Party Cake | 28,000 | cake | MEDIUM |
| Galle Gateaux | orders@gategaux.lk | Fondant Signature Cake | 36,000 | cake | HIGH |

### Catering
| Vendor | Vendor Email | Offering | Price (LKR) | Unit | Quality |
| --- | --- | --- | --- | --- | --- |
| Cinnamon Catering | sales@cinnamoncatering.lk | Premium Buffet Menu | 3,200 | per_head | HIGH |
| Kandy Banquet Caterers | orders@kandybanquet.lk | Classic Banquet Menu | 2,200 | per_head | MEDIUM |
| Southern Feast Catering | orders@southernfeast.lk | Seafood & BBQ Spread | 2,600 | per_head | HIGH |

### Drinks & Bar
| Vendor | Vendor Email | Offering | Price (LKR) | Unit | Quality |
| --- | --- | --- | --- | --- | --- |
| Lanka Mobile Bar | events@lankamobilebar.lk | Mobile Bar Package | 95,000 | event | HIGH |
| Colombo Mocktail Lab | events@mocktaillab.lk | Signature Mocktail Station | 65,000 | event | MEDIUM |
| Hill Country Beverage Co. | events@hillcountrybev.lk | Tea & Refreshment Bar | 35,000 | event | LOW |

### DJ & Music
| Vendor | Vendor Email | Offering | Price (LKR) | Unit | Quality |
| --- | --- | --- | --- | --- | --- |
| DJ Pulse Colombo | dj@djpulse.lk | DJ Set (4 Hours) | 65,000 | event | HIGH |
| Kandy Night Beats | dj@kandynightbeats.lk | DJ + MC Package | 48,000 | event | MEDIUM |
| Galle Groove DJs | dj@groovedjs.lk | Beach Party DJ Set | 52,000 | event | MEDIUM |

### Photography & Videography
| Vendor | Vendor Email | Offering | Price (LKR) | Unit | Quality |
| --- | --- | --- | --- | --- | --- |
| Tisal Photography | tisal.20221672@iit.ac.lk | Basic Photography Package | 45,000 | event | LOW |
| Tisal Photography | tisal.20221672@iit.ac.lk | Standard Photo + Video | 85,000 | event | MEDIUM |
| Tisal Photography | tisal.20221672@iit.ac.lk | Premium Storytelling Suite | 150,000 | event | HIGH |
| Lanka Lens Studio | book@lankalens.lk | Studio Photography Coverage | 60,000 | event | MEDIUM |
| Moment Makers LK | book@momentmakers.lk | Highlight Film Package | 72,000 | event | MEDIUM |

### Band & Live Music
| Vendor | Vendor Email | Offering | Price (LKR) | Unit | Quality |
| --- | --- | --- | --- | --- | --- |
| Colombo Jazz Quintet | bookings@colombojazz.lk | Live Jazz Band (4 Hours) | 85,000 | event | HIGH |
| Kandy Acoustic Trio | book@kandyacoustic.lk | Acoustic Live Set | 48,000 | event | MEDIUM |
| Southern Sunset Band | book@southernsunsetband.lk | Live Band (3 Hours) | 62,000 | event | MEDIUM |

### Entertainment
| Vendor | Vendor Email | Offering | Price (LKR) | Unit | Quality |
| --- | --- | --- | --- | --- | --- |
| Magician Nimal | book@magiciannimal.lk | Magic & Illusion Show | 55,000 | event | HIGH |
| Fire Show LK | book@fireshowlk.lk | Fire Dance Performance | 70,000 | event | HIGH |
| Kids Party Fun Crew | book@kidsfuncrew.lk | Kids Entertainment Set | 35,000 | event | LOW |

### Floral Arrangements
| Vendor | Vendor Email | Offering | Price (LKR) | Unit | Quality |
| --- | --- | --- | --- | --- | --- |
| Colombo Bloom Studio | orders@colombobloom.lk | Premium Floral Set | 125,000 | event | HIGH |
| Kandy Orchid House | orders@kandyorchid.lk | Orchid Table Styling | 65,000 | event | MEDIUM |
| Galle Garden Florals | orders@gallegardenflorals.lk | Garden Arch & Bouquet | 85,000 | event | MEDIUM |

### Event Decoration
| Vendor | Vendor Email | Offering | Price (LKR) | Unit | Quality |
| --- | --- | --- | --- | --- | --- |
| Pearl Event Decor | book@pearleventdecor.lk | Luxury Event Styling | 180,000 | event | HIGH |
| Ceylon Party Styling | book@ceylonpartystyling.lk | Classic Theme Decor | 95,000 | event | MEDIUM |
| Golden Arch Decor | book@goldenarchdecor.lk | Outdoor Event Decor | 110,000 | event | MEDIUM |

### Venue & Spaces
| Vendor | Vendor Email | Offering | Price (LKR) | Unit | Quality |
| --- | --- | --- | --- | --- | --- |
| Galle Face Hotel | events@gallefacehotel.lk | Grand Ballroom | 500,000 | event | HIGH |
| Mount Lavinia Hotel | weddings@mountlaviniahotel.lk | Oceanfront Lawn | 380,000 | event | HIGH |
| The Wallawwa | events@wallawwa.lk | Heritage Courtyard Venue | 420,000 | event | HIGH |

### Transport
| Vendor | Vendor Email | Offering | Price (LKR) | Unit | Quality |
| --- | --- | --- | --- | --- | --- |
| Colombo Limo Service | book@colombolimo.lk | Luxury Sedan Transfer | 28,000 | trip | HIGH |
| Kandy Vintage Rides | book@kandyvintage.lk | Classic Car Entrance | 35,000 | event | MEDIUM |
| Southern Shuttle Co. | book@southernshuttle.lk | Guest Shuttle Service | 45,000 | event | MEDIUM |
