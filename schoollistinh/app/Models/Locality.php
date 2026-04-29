<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Locality extends Model
{
    use HasFactory;

    protected $fillable = [
        'city_id',
        'name',
        'slug',
        'school_count',
        'is_active',
    ];

    protected $casts = [
        'is_active' => 'boolean',
        'school_count' => 'integer',
    ];

    public function city(): BelongsTo
    {
        return $this->belongsTo(City::class);
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

    public function getRouteKeyName(): string
    {
        return 'slug';
    }

    public function getFullNameAttribute(): string
    {
        return $this->name . ', ' . $this->city->name;
    }
}
