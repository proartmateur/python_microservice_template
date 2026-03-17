/**
 * @author Enrique Nieto <myself@example.com>
 * @date 2026-03-17 17:21:15.557537900 UTC
 */

import { Petra } from './Petra';
import { PetraDTO } from './PetraDTO';

/**
 * Repository interface for Petra entity
 */
export interface IPetraRepository {
    /**
     * Find entity by ID
     */
    findById(id: string): Promise<Petra | null>;
    
    /**
     * Find all entities
     */
    findAll(): Promise<Petra[]>;
    
    /**
     * Save entity
     */
    save(entity: Petra): Promise<void>;
    
    /**
     * Create from DTO
     */
    create(dto: PetraDTO): Promise<Petra>;
    
    /**
     * Update entity
     */
    update(id: string, dto: PetraDTO): Promise<Petra>;
    
    /**
     * Delete entity
     */
    delete(id: string): Promise<void>;
}
