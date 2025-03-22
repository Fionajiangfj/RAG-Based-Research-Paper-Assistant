import React from 'react';
import { Box, Text, VStack, Heading, Divider } from '@chakra-ui/react';
import { QueryResponse } from '../types';
import { SourceCitation } from './SourceCitation';

interface ResultDisplayProps {
  result: QueryResponse;
}

export const ResultDisplay = ({ result }: ResultDisplayProps) => {
  return (
    <Box p={6} borderWidth="1px" borderRadius="lg" boxShadow="md">
      <VStack spacing={6} align="stretch">
        <Heading size="md">Query Result</Heading>
        <Text fontSize="lg">{result.answer}</Text>
        <Divider />
        <Heading size="sm">Sources</Heading>
        <VStack spacing={4} align="stretch">
          {result.source_nodes.map((node, index) => (
            <SourceCitation key={index} node={node} />
          ))}
        </VStack>
      </VStack>
    </Box>
  );
};
