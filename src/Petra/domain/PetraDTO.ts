/**
 * @author Enrique Nieto <myself@example.com>
 * @date 2026-03-17 17:18:00.646250100 UTC
 */

/**
 * Data Transfer Object for Petra
 * Used for data transmission between layers
 */
export interface PetraDTO {
   name: string;
   user: number;

}

/**
 * Create a new PetraDTO
 */
export function createPetraDTO(
   name: string,
   user: number,

): PetraDTO {
    return {
       name,
       user,

    };
}
