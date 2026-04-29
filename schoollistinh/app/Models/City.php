<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Support\Collection;
use Illuminate\Support\Facades\Cache;

class City extends Model
{
    use HasFactory;

    protected $fillable = [
        'name',
        'slug',
        'state_name',
        'country_name',
        'school_count',
        'is_active',
        'description',
    ];

    protected $casts = [
        'is_active' => 'boolean',
        'school_count' => 'integer',
    ];

    public function localities(): HasMany
    {
        return $this->hasMany(Locality::class);
    }

    public function schools(): HasMany
    {
        return $this->hasMany(School::class);
    }

    public function activeSchools(): HasMany
    {
        return $this->schools()->where('is_active', true);
    }

    public function scopeActive($query)
    {
        return $query->where('is_active', true);
    }

    public function scopeWithSchools($query)
    {
        return $query->where('school_count', '>', 0);
    }

    public static function navMenuCities(int $limit = 11): Collection
    {
        return Cache::remember('nav_menu_cities:'.$limit, now()->addMinutes(15), function () use ($limit) {
            $cities = static::active()
                ->withSchools()
                ->orderByDesc('school_count')
                ->orderBy('name')
                ->limit($limit)
                ->get();

            // Pin popular cities first
            $pinnedSlugs = ['delhi', 'mumbai', 'bangalore', 'hyderabad', 'chennai', 'pune', 'gurugram', 'noida'];
            $ordered = collect();
            $usedIds = [];

            foreach ($pinnedSlugs as $slug) {
                $city = $cities->first(fn ($c) => $c->slug === $slug);
                if ($city && !isset($usedIds[$city->id])) {
                    $ordered->push($city);
                    $usedIds[$city->id] = true;
                }
            }

            foreach ($cities as $city) {
                if (!isset($usedIds[$city->id])) {
                    $ordered->push($city);
                }
            }

            return $ordered->take($limit)->values();
        });
    }

    public static function featuredCities(): Collection
    {
        return Cache::remember('featured_cities', now()->addMinutes(30), function () {
            return static::active()
                ->withSchools()
                ->whereIn('slug', ['delhi', 'mumbai', 'bangalore', 'hyderabad', 'chennai', 'pune', 'gurugram', 'noida', 'kolkata', 'jaipur'])
                ->orderByDesc('school_count')
                ->get();
        });
    }

    public function getRouteKeyName(): string
    {
        return 'slug';
    }
}
