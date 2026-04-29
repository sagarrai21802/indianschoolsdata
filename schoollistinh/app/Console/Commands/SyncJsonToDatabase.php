<?php

namespace App\Console\Commands;

use App\Models\City;
use App\Models\Locality;
use App\Models\School;
use App\Models\Facility;
use App\Repositories\SchoolRepository;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\DB;

class SyncJsonToDatabase extends Command
{
    protected $signature = 'schools:sync-json {--clear : Clear existing data before sync}';
    protected $description = 'Sync school data from JSON files to database';

    private SchoolRepository $repository;
    private int $citiesCreated = 0;
    private int $localitiesCreated = 0;
    private int $schoolsCreated = 0;
    private int $facilitiesCreated = 0;

    public function handle(SchoolRepository $repository): int
    {
        $this->repository = $repository;

        $this->info('Starting JSON to Database sync...');

        if ($this->option('clear')) {
            $this->warn('Clearing existing data...');
            DB::table('school_facility')->delete();
            School::query()->delete();
            Locality::query()->delete();
            City::query()->delete();
        }

        $cities = $repository->getCities();
        
        $this->info("Found {$cities->count()} cities to process");

        $bar = $this->output->createProgressBar($cities->count());
        $bar->start();

        foreach ($cities as $cityData) {
            $this->processCity($cityData);
            $bar->advance();
        }

        $bar->finish();
        $this->newLine();

        // Update counts
        $this->updateCounts();

        $this->info('Sync completed!');
        $this->table(
            ['Entity', 'Created'],
            [
                ['Cities', $this->citiesCreated],
                ['Localities', $this->localitiesCreated],
                ['Schools', $this->schoolsCreated],
                ['Facilities', $this->facilitiesCreated],
            ]
        );

        return Command::SUCCESS;
    }

    private function processCity(array $cityData): void
    {
        $city = City::firstOrCreate(
            ['slug' => $cityData['slug']],
            [
                'name' => $cityData['name'],
                'school_count' => $cityData['school_count'],
                'is_active' => true,
            ]
        );

        if ($city->wasRecentlyCreated) {
            $this->citiesCreated++;
        }

        // Process schools in city
        $page = 1;
        do {
            $result = $this->repository->getSchoolsByCity($cityData['slug'], $page, 100);
            
            foreach ($result['schools'] as $schoolData) {
                $this->processSchool($city, $schoolData);
            }
            
            $page++;
        } while ($page <= $result['pages']);
    }

    private function processSchool(City $city, array $schoolData): void
    {
        // Get or create locality
        $locality = null;
        if (!empty($schoolData['locality'])) {
            $localitySlug = str_replace(' ', '-', strtolower($schoolData['locality']));
            
            $locality = Locality::firstOrCreate(
                ['city_id' => $city->id, 'slug' => $localitySlug],
                [
                    'name' => $schoolData['locality'],
                    'is_active' => true,
                ]
            );

            if ($locality->wasRecentlyCreated) {
                $this->localitiesCreated++;
            }
        }

        // Create or update school
        $school = School::updateOrCreate(
            ['city_id' => $city->id, 'slug' => $schoolData['slug']],
            [
                'locality_id' => $locality?->id,
                'name' => $schoolData['name'],
                'address' => $schoolData['address'],
                'locality_name' => $schoolData['locality'],
                'board' => $schoolData['board'],
                'medium' => $schoolData['medium'],
                'school_type' => $schoolData['school_type'],
                'fees_min' => $schoolData['fees_min'],
                'fees_max' => $schoolData['fees_max'],
                'fees_currency' => $schoolData['fees_currency'],
                'fees_text' => $schoolData['fees_text'],
                'phone' => $schoolData['phone'],
                'email' => $schoolData['email'],
                'website' => $schoolData['website'],
                'rating' => $schoolData['rating'],
                'reviews_count' => $schoolData['reviews_count'],
                'images' => $schoolData['images'],
                'admission_status' => $schoolData['admission_status'],
                'is_active' => true,
            ]
        );

        if ($school->wasRecentlyCreated) {
            $this->schoolsCreated++;
        }

        // Process facilities
        if (!empty($schoolData['facilities'])) {
            $facilityIds = [];
            foreach ($schoolData['facilities'] as $facilityName) {
                $facility = $this->getOrCreateFacility($facilityName);
                $facilityIds[] = $facility->id;
            }
            $school->facilities()->sync($facilityIds);
        }
    }

    private function getOrCreateFacility(string $name): Facility
    {
        $slug = str_replace(' ', '-', strtolower($name));
        
        $facility = Facility::firstOrCreate(
            ['slug' => $slug],
            [
                'name' => $name,
                'is_active' => true,
            ]
        );

        if ($facility->wasRecentlyCreated) {
            $this->facilitiesCreated++;
        }

        return $facility;
    }

    private function updateCounts(): void
    {
        // Update city counts
        foreach (City::all() as $city) {
            $city->update(['school_count' => $city->schools()->count()]);
        }

        // Update locality counts
        foreach (Locality::all() as $locality) {
            $locality->update(['school_count' => $locality->schools()->count()]);
        }
    }
}
