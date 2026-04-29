<?php

namespace App\Repositories;

use Illuminate\Support\Collection;
use Illuminate\Support\Facades\File;
use Illuminate\Support\Facades\Cache;

class SchoolRepository
{
    private string $basePath;

    public function __construct()
    {
        $this->basePath = storage_path('app/schools');
    }

    public function getCities(): Collection
    {
        return Cache::remember('schools:cities', now()->addHour(), function () {
            $cities = collect();
            
            if (!File::isDirectory($this->basePath)) {
                return $cities;
            }

            foreach (File::directories($this->basePath) as $cityPath) {
                $citySlug = basename($cityPath);
                $cityFile = $cityPath . '/_city.json';
                
                if (File::exists($cityFile)) {
                    $data = json_decode(File::get($cityFile), true);
                    if ($data) {
                        $cities->push([
                            'slug' => $citySlug,
                            'name' => $this->formatCityName($citySlug),
                            'school_count' => $data['total_schools'] ?? 0,
                            'raw' => $data,
                        ]);
                    }
                }
            }

            return $cities->sortBy('name')->values();
        });
    }

    public function getCity(string $slug): ?array
    {
        $cityFile = $this->basePath . '/' . $slug . '/_city.json';
        
        if (!File::exists($cityFile)) {
            return null;
        }

        $data = json_decode(File::get($cityFile), true);
        if (!$data) {
            return null;
        }

        return [
            'slug' => $slug,
            'name' => $this->formatCityName($slug),
            'school_count' => $data['total_schools'] ?? 0,
            'raw' => $data,
        ];
    }

    public function getSchoolsByCity(string $citySlug, int $page = 1, int $perPage = 20): array
    {
        $cacheKey = "schools:city:{$citySlug}:page:{$page}";
        
        return Cache::remember($cacheKey, now()->addMinutes(30), function () use ($citySlug, $page, $perPage) {
            $cityPath = $this->basePath . '/' . $citySlug;
            
            if (!File::isDirectory($cityPath)) {
                return ['schools' => collect(), 'total' => 0, 'pages' => 0];
            }

            $schools = collect();
            
            foreach (File::directories($cityPath) as $schoolPath) {
                $schoolSlug = basename($schoolPath);
                
                // Skip _city.json and other non-school directories
                if (str_starts_with($schoolSlug, '_') || str_starts_with($schoolSlug, '.')) {
                    continue;
                }

                $aboutFile = $schoolPath . '/about.json';
                
                if (File::exists($aboutFile)) {
                    $data = json_decode(File::get($aboutFile), true);
                    if ($data) {
                        $schools->push($this->normalizeSchoolData($data, $citySlug));
                    }
                }
            }

            $total = $schools->count();
            $pages = (int) ceil($total / $perPage);
            
            $paginated = $schools->slice(($page - 1) * $perPage, $perPage)->values();

            return [
                'schools' => $paginated,
                'total' => $total,
                'pages' => $pages,
                'current_page' => $page,
            ];
        });
    }

    public function getSchool(string $citySlug, string $schoolSlug): ?array
    {
        $cacheKey = "schools:detail:{$citySlug}:{$schoolSlug}";
        
        return Cache::remember($cacheKey, now()->addHour(), function () use ($citySlug, $schoolSlug) {
            $aboutFile = $this->basePath . '/' . $citySlug . '/' . $schoolSlug . '/about.json';
            
            if (!File::exists($aboutFile)) {
                return null;
            }

            $data = json_decode(File::get($aboutFile), true);
            if (!$data) {
                return null;
            }

            return $this->normalizeSchoolData($data, $citySlug, true);
        });
    }

    public function searchSchools(string $query, ?string $citySlug = null, array $filters = []): Collection
    {
        $cities = $citySlug ? [$citySlug] : $this->getCities()->pluck('slug')->toArray();
        
        $results = collect();
        
        foreach ($cities as $city) {
            $cityData = $this->getSchoolsByCity($city, 1, 1000);
            
            foreach ($cityData['schools'] as $school) {
                // Apply text search
                if ($query) {
                    $searchable = strtolower($school['name'] . ' ' . ($school['locality'] ?? '') . ' ' . ($school['board'] ?? ''));
                    if (!str_contains($searchable, strtolower($query))) {
                        continue;
                    }
                }
                
                // Apply filters
                if (!empty($filters['board']) && ($school['board'] ?? '') !== $filters['board']) {
                    continue;
                }
                
                if (!empty($filters['type']) && ($school['school_type'] ?? '') !== $filters['type']) {
                    continue;
                }
                
                if (!empty($filters['locality']) && ($school['locality'] ?? '') !== $filters['locality']) {
                    continue;
                }
                
                $results->push($school);
            }
        }
        
        return $results;
    }

    public function getSchoolsByLocality(string $citySlug, string $locality): Collection
    {
        $allSchools = $this->getSchoolsByCity($citySlug, 1, 1000);
        
        return $allSchools['schools']->filter(function ($school) use ($locality) {
            return strtolower($school['locality'] ?? '') === strtolower($locality);
        })->values();
    }

    public function getLocalitiesInCity(string $citySlug): Collection
    {
        $cacheKey = "localities:city:{$citySlug}";
        
        return Cache::remember($cacheKey, now()->addHour(), function () use ($citySlug) {
            $schools = $this->getSchoolsByCity($citySlug, 1, 1000);
            
            return $schools['schools']
                ->groupBy('locality')
                ->map(function ($group, $locality) {
                    return [
                        'name' => $locality,
                        'slug' => str_replace(' ', '-', strtolower($locality)),
                        'school_count' => $group->count(),
                    ];
                })
                ->sortBy('name')
                ->values();
        });
    }

    public function clearCache(): void
    {
        Cache::flush();
    }

    private function normalizeSchoolData(array $data, string $citySlug, bool $full = false): array
    {
        $normalized = [
            'id' => $data['id'] ?? '',
            'name' => $data['name'] ?? '',
            'slug' => basename($data['slug'] ?? ''),
            'city' => $citySlug,
            'locality' => $data['locality'] ?? '',
            'address' => $data['address'] ?? '',
            'board' => $data['board'] ?? '',
            'medium' => $data['medium'] ?? '',
            'school_type' => $data['school_type'] ?? '',
            'rating' => $data['rating'] ?? null,
            'reviews_count' => $data['reviews_count'] ?? 0,
            'fees_min' => $data['fees']['min'] ?? null,
            'fees_max' => $data['fees']['max'] ?? null,
            'fees_currency' => $data['fees']['currency'] ?? 'INR',
            'fees_text' => $data['fees_text'] ?? '',
            'phone' => $data['contact']['phone'] ?? '',
            'email' => $data['contact']['email'] ?? '',
            'website' => $data['contact']['website'] ?? '',
            'images' => $data['images'] ?? [],
            'facilities' => $data['facilities'] ?? [],
            'admission_status' => $data['admission']['status'] ?? 'unknown',
        ];

        if ($full) {
            $normalized['raw'] = $data;
            $normalized['established'] = $data['established'] ?? '';
            $normalized['grades'] = $data['grades'] ?? '';
            $normalized['listing_only'] = $data['listing_only'] ?? true;
            $normalized['listing_page'] = $data['listing_page'] ?? '';
            $normalized['scraped_at'] = $data['scraped_at'] ?? null;
        }

        return $normalized;
    }

    private function formatCityName(string $slug): string
    {
        return ucwords(str_replace(['-', '_'], ' ', $slug));
    }
}
