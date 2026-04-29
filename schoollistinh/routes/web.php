<?php

use App\Http\Controllers\HomeController;
use App\Http\Controllers\SchoolController;
use App\Http\Controllers\CityController;
use App\Http\Controllers\LocalityController;
use App\Http\Controllers\SearchController;
use App\Http\Controllers\ProgrammaticSeoController;
use App\Http\Controllers\InquiryController;
use App\Http\Controllers\SitemapController;
use Illuminate\Support\Facades\Route;

/*
|--------------------------------------------------------------------------
| Web Routes
|--------------------------------------------------------------------------
*/

// Homepage
Route::get('/', [HomeController::class, 'index'])->name('home');

// All cities listing
Route::get('/schools', [SchoolController::class, 'index'])->name('schools.index');

// City listing page
Route::get('/schools/{city}', [CityController::class, 'show'])->name('city.show');

// Locality listing page
Route::get('/schools/{city}/{locality}', [LocalityController::class, 'show'])->name('locality.show');

// School detail page
Route::get('/school/{city}/{school}', [SchoolController::class, 'show'])->name('school.show');

// Search
Route::get('/search', [SearchController::class, 'index'])->name('search');

// Programmatic SEO pages - Board specific
Route::get('/cbse-schools-in-{city}', [ProgrammaticSeoController::class, 'cbse'])->name('seo.cbse');
Route::get('/icse-schools-in-{city}', [ProgrammaticSeoController::class, 'icse'])->name('seo.icse');
Route::get('/state-board-schools-in-{city}', [ProgrammaticSeoController::class, 'stateBoard'])->name('seo.state-board');

// Programmatic SEO pages - Type specific
Route::get('/play-schools-in-{city}', [ProgrammaticSeoController::class, 'playSchool'])->name('seo.play-school');
Route::get('/primary-schools-in-{city}', [ProgrammaticSeoController::class, 'primary'])->name('seo.primary');
Route::get('/secondary-schools-in-{city}', [ProgrammaticSeoController::class, 'secondary'])->name('seo.secondary');
Route::get('/senior-secondary-schools-in-{city}', [ProgrammaticSeoController::class, 'seniorSecondary'])->name('seo.senior-secondary');

// Programmatic SEO pages - Rating/Fee based
Route::get('/top-rated-schools-in-{city}', [ProgrammaticSeoController::class, 'topRated'])->name('seo.top-rated');

// Inquiry form
Route::get('/inquiry/{city}/{school}', [InquiryController::class, 'create'])->name('inquiry.create');
Route::post('/inquiry', [InquiryController::class, 'store'])->name('inquiry.store');

// Sitemap
Route::get('/sitemap.xml', [SitemapController::class, 'index'])->name('sitemap');

// Static pages
Route::get('/about', function () {
    return view('pages.about');
})->name('about');

Route::get('/contact', function () {
    return view('pages.contact');
})->name('contact');

Route::get('/privacy', function () {
    return view('pages.privacy');
})->name('privacy');
