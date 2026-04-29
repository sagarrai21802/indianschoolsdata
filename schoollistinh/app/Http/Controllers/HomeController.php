<?php

namespace App\Http\Controllers;

use App\Models\City;
use App\Models\School;
use App\Repositories\SchoolRepository;

class HomeController extends Controller
{
    public function index(SchoolRepository $repository)
    {
        $featuredCities = $this->getFeaturedCities($repository);
        
        $totalSchools = School::active()->count();
        $totalCities = City::active()->withSchools()->count();
        
        // Get some featured schools
        $featuredSchools = School::active()
            ->with(['city', 'locality'])
            ->inRandomOrder()
            ->limit(8)
            ->get();

        return view('pages.home', compact(
            'featuredCities',
            'totalSchools',
            'totalCities',
            'featuredSchools'
        ));
    }

    private function getFeaturedCities(SchoolRepository $repository)
    {
        // Try to get from database first
        $cities = City::active()
            ->withSchools()
            ->whereIn('slug', ['delhi', 'mumbai', 'bangalore', 'hyderabad', 'chennai', 'pune', 'kolkata', 'jaipur'])
            ->orderByDesc('school_count')
            ->get();

        // If database is empty, fall back to JSON
        if ($cities->isEmpty()) {
            $jsonCities = $repository->getCities();
            $featuredSlugs = ['delhi', 'mumbai', 'bangalore', 'hyderabad', 'chennai', 'pune', 'kolkata', 'jaipur'];
            
            $cities = $jsonCities
                ->filter(fn ($city) => in_array($city['slug'], $featuredSlugs))
                ->sortByDesc('school_count')
                ->map(fn ($city) => (object) $city);
        }

        return $cities;
    }
}
