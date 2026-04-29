# SchoolList - School Directory Application

A Laravel-based school directory application that lists schools across India. Built to replicate the functionality of the reference coworking space app but adapted for school listings.

## Features

- **Browse Schools by City**: View schools organized by city and locality
- **School Detail Pages**: Comprehensive information including fees, contact details, facilities
- **Search & Filter**: Search by name, city, board type (CBSE, ICSE, State Board)
- **SEO Programmatic Pages**: Pre-built pages for CBSE schools, ICSE schools, play schools, etc.
- **Admin Panel**: Filament-based admin for managing schools, cities, and content
- **JSON Data Source**: Primary data stored in JSON files with database sync for admin
- **Inquiry Forms**: Parents can submit admission inquiries to schools
- **Responsive Design**: Mobile-friendly UI with Tailwind CSS

## Project Structure

```
schoollistinh/
├── app/
│   ├── Console/Commands/      # CLI commands for data sync
│   ├── Filament/Resources/    # Admin panel resources
│   ├── Http/Controllers/      # Web controllers
│   ├── Models/                # Eloquent models
│   └── Repositories/          # School data repository
├── config/
├── database/migrations/         # Database schema
├── resources/views/           # Blade templates
├── routes/web.php             # Application routes
└── storage/app/schools/       # JSON data files
```

## Installation

### 1. Install PHP Dependencies

```bash
cd schoollistinh
composer install
```

### 2. Setup Environment

```bash
cp .env.example .env
php artisan key:generate
```

### 3. Setup Database

```bash
touch database/database.sqlite
php artisan migrate
```

### 4. Copy School Data

```bash
php artisan schools:setup
```

This copies the scraped data from `../scraped_data` to `storage/app/schools/`.

### 5. Sync to Database (for Admin Panel)

```bash
php artisan schools:sync-json
```

This imports the JSON data into the database tables.

### 6. Install Node Dependencies

```bash
npm install
npm run build
```

### 7. Create Admin User

```bash
php artisan make:filament-user
```

### 8. Start the Application

```bash
php artisan serve
```

Visit http://localhost:8000

Admin panel: http://localhost:8000/admin

## Available Commands

| Command | Description |
|---------|-------------|
| `php artisan schools:setup` | Copy scraped_data to storage/app/schools |
| `php artisan schools:sync-json` | Import JSON data to database |
| `php artisan schools:export-json` | Export DB changes back to JSON |
| `php artisan schools:cache-warm` | Pre-cache popular pages |

## URL Structure

| Route | Description |
|-------|-------------|
| `/` | Homepage with city search |
| `/schools` | All cities listing |
| `/schools/{city}` | Schools in a city |
| `/schools/{city}/{locality}` | Schools in locality |
| `/school/{city}/{slug}` | School detail page |
| `/search` | Search with filters |
| `/cbse-schools-in-{city}` | CBSE schools by city |
| `/icse-schools-in-{city}` | ICSE schools by city |
| `/admin/*` | Filament admin panel |

## Data Flow

```
scraped_data/ (source JSON)
    ↓
storage/app/schools/ (app storage)
    ↓ (read by)
SchoolRepository (file-based access)
    ↓ (sync to)
Database (for Filament admin)
```

## Technologies Used

- **Laravel 11** - PHP framework
- **Filament 3** - Admin panel
- **Tailwind CSS** - Styling
- **Vite** - Build tool
- **SQLite** - Default database (can use MySQL/PostgreSQL)

## Next Steps

1. Run `composer install` to install PHP dependencies
2. Run `npm install && npm run build` for frontend assets
3. Run `php artisan schools:setup` to copy data
4. Run `php artisan schools:sync-json` to populate database
5. Create admin user with `php artisan make:filament-user`
6. Start server with `php artisan serve`

## Credits

Built based on the reference coworking space application architecture.
